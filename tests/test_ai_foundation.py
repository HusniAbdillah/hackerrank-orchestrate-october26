import json
import time
from dataclasses import replace

import pytest

from deletion_audit.ai_config import ProviderConfig, load_dotenv
from deletion_audit.ai_auditor import AuditInvestigator
from deletion_audit.inputs import InputError
from deletion_audit.investigator import AuditTools
from deletion_audit.observations import EvidenceStore
from deletion_audit.policy import Policy
from deletion_audit.proposals import PROPOSAL_SCHEMA, ground_fact, validate_json
from deletion_audit.providers import Provider, ProviderError, UsageLedger
from deletion_audit.solver import audit, profile_scope_proofs
from test_solver import ROOT, AT, graph, obs, request


def api_tools():
    store = EvidenceStore()
    store.add([obs(fields={"user_id": "user_fixture"})])
    return AuditTools(request(), store, graph(), Policy.load(ROOT / "dataset"))


def fact(source):
    return dict(system_id=source.system_id, resource_id=source.resource_id, evidence_id=source.source_id,
                observation_id=source.observation_id, observed_at=source.observed_at.isoformat(),
                category=source.category, state="PRESENT", interpretation="REUSE_DIRECT", fact_or_hypothesis="FACT",
                quote="user_fixture", attributes={}, reasoning_summary="Literal subject identifier in a direct record.")


def proposal(facts=None):
    return {"facts": facts or [], "hypotheses": [], "unresolved_questions": [], "summary": "Source-backed review"}


def chat(text="", calls=None):
    message = {"role": "assistant", "content": text}
    if calls:
        message["tool_calls"] = calls
    return {"model": "deepseek-flash", "choices": [{"message": message}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20}}


def test_explicit_empty_primary_scope_can_supplement_retained_checks():
    store = EvidenceStore()
    store.add([obs("SECURITY_AUDIT_LOG", {"user_id": "user_fixture"}, "journal", "security_service")])
    assert audit(request(), store, graph(), Policy.load(ROOT / "dataset"))[2]["abstained"]
    empty = replace(obs(), resource_id=None, kind="scoped_negative", fields={}, scope={
        "complete_collection": True, "table": "customer_profiles", "snapshot_scope": [{"origin_system": "account_service"}]})
    store.add([empty])
    status, steps, diagnostic = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert status == "COMPLETE" and not diagnostic["abstained"]
    assert steps[0]["operation"] == "VERIFY_RECORD_PRESENT" and diagnostic["scope_proofs"]
    assert not any(s["resource_id"] == "invented_profile" for s in steps)


@pytest.mark.parametrize("future,covered", [(True, True), (False, False)])
def test_primary_scope_proof_requires_availability_and_declared_service(future, covered):
    store = EvidenceStore(); store.add([obs("SECURITY_AUDIT_LOG", {"user_id": "user_fixture"}, "journal", "security_service")])
    empty = replace(obs(capture="2026-02-02T00:00:00Z" if future else "2026-01-20T00:00:00Z"),
                    resource_id=None, kind="scoped_negative", fields={}, scope={"complete_collection": True,
                    "snapshot_scope": [{"origin_system": "account_service" if covered else "search_service"}]})
    store.add([empty])
    assert audit(request(), store, graph(), Policy.load(ROOT / "dataset"))[2]["abstained"]


def test_declared_inventory_subject_filter_rejects_anonymous_or_matching_rows():
    from deletion_audit.identity import IdentityGraph
    from test_identity import snapshot
    identities = IdentityGraph([snapshot("user_fixture", "person@example.test"), snapshot("user_other", "other@example.test")], [])
    scope = {"table": "customer_profiles", "snapshot_scope": [{"origin_system": "account_service"}]}
    other = obs(fields={"user_id": "user_other"}, scope=scope)
    store = EvidenceStore(); store.add([other])
    assert profile_scope_proofs(store, AT, identities, "user_fixture")
    anonymous = replace(other, observation_id="anonymous", identifiers=(), fields={"email": None})
    store.add([anonymous])
    assert not profile_scope_proofs(store, AT, identities, "user_fixture")


def test_credentials_are_not_in_config_repr_or_dotenv_overrides(tmp_path, monkeypatch):
    path = tmp_path / ".env"; path.write_text('GEMINI_API_KEY="unit-test-only"\nLLM_ENABLED=true\n')
    monkeypatch.setenv("GEMINI_API_KEY", "environment-wins")
    load_dotenv(path)
    cfg = ProviderConfig.load("gemini")
    assert cfg.key == "environment-wins" and "environment-wins" not in repr(cfg)


def test_normalized_deepseek_tool_call_and_token_accounting():
    ledger = UsageLedger(max_calls=1)
    calls = [{"id": "x", "type": "function", "function": {"name": "trace_identity", "arguments": "{}"}}]
    provider = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test", .3, 1.2), ledger,
                        lambda *args: chat(calls=calls))
    response = provider.complete([{"role": "user", "content": "Fictional request"}])
    assert response.calls == [{"id": "x", "name": "trace_identity", "arguments": {}}]
    assert ledger.summary()["input_tokens"] == 100 and ledger.summary()["calls"] == 1
    with pytest.raises(ProviderError, match="BUDGET"):
        provider.complete([{"role": "user", "content": "Another request"}])


def test_gemini_thought_signatures_preserved_and_usage_includes_thought_tokens():
    payload = {"candidates": [{"content": {"parts": [{"functionCall": {"name": "trace_identity", "args": {}}, "thoughtSignature": "opaque-state"}]}}],
               "usageMetadata": {"promptTokenCount": 40, "candidatesTokenCount": 10, "thoughtsTokenCount": 5}}
    provider = Provider(ProviderConfig("gemini", "gemini-3.8-flash", "unit-test"), UsageLedger(), lambda *args: payload)
    reply = provider.complete([{"role": "user", "content": "Inspect"}])
    _, body, _ = provider._request([reply.assistant], None, None)
    assert body["contents"][0]["parts"][0]["thoughtSignature"] == "opaque-state"
    assert reply.usage["output_tokens"] == 15


def test_retry_is_bounded_and_error_does_not_contain_credentials(monkeypatch):
    attempts = []
    def failing(*args):
        attempts.append(1); raise ProviderError("HTTP_429", True)
    monkeypatch.setattr(time, "sleep", lambda _: None)
    ledger = UsageLedger()
    provider = Provider(ProviderConfig("deepseek", "deepseek-flash", "private-unit-key", retries=1), ledger, failing)
    with pytest.raises(ProviderError): provider.complete([{"role": "user", "content": "Inspect"}])
    assert len(attempts) == 2 and ledger.summary()["errors"] == 2
    assert "private-unit-key" not in json.dumps(ledger.records)


@pytest.mark.parametrize("change", [{"evidence_id": "invented"}, {"state": "ABSENT"}, {"observed_at": "2030-01-01T00:00:00Z"},
                                    {"resource_id": "another_resource"}, {"fact_or_hypothesis": "HYPOTHESIS"}, {"quote": "invented quote"}])
def test_proposal_grounding_rejects_invented_or_unsupported_facts(change):
    tools = api_tools(); value = fact(tools.store.observations[0]); value.update(change)
    with pytest.raises(InputError): ground_fact(value, tools)


def test_schema_forbids_model_verdicts_and_unknown_actions():
    value = proposal(); value["deletion_status"] = "COMPLETE"
    with pytest.raises(InputError): validate_json(value, PROPOSAL_SCHEMA)


def test_activity_success_cannot_become_direct_state():
    tools = api_tools(); source = replace(tools.store.observations[0], kind="reported_claim")
    tools.store.observations[0] = source
    with pytest.raises(InputError, match="CLAIM"):
        ground_fact(fact(source), tools)


def test_asset_proposal_needs_literal_file_and_explicit_sole_owner_link():
    from deletion_audit.observations import identifiers
    tools = api_tools()
    link = obs(fields={"event_type": "LINK_RESOURCE_IDENTITY", "details":
        "Attachment catalog confirmed opaque (receipt.pdf) belongs only to person@example.test and user_fixture; no other subject is linked."}, kind="reported_claim")
    link = replace(link, observation_id="activity_8", source_id="activity_8")
    context = replace(obs(fields={"text": "Objects receipt.pdf version v3"}), observation_id="listing", system_id=None,
                      resource_id=None, kind="context", category=None, collection="ocr_text", identifiers=())
    tools.store.add([link, context])
    value = fact(tools.store.observations[0])
    value.update(interpretation="LINK_ASSET", category="SUPPORT_ATTACHMENT", observation_id="listing",
                 quote="receipt.pdf", attributes={"asset_reference": "receipt.pdf", "link_evidence_id": "activity_8"})
    result = ground_fact(value, tools)
    assert result.kind == "direct" and result.category == "SUPPORT_ATTACHMENT" and result.source_id == context.source_id
    value["attributes"]["asset_reference"] = "someone_else.pdf"
    with pytest.raises(InputError): ground_fact(value, tools)


def test_vision_cannot_use_a_different_source_hash():
    tools = api_tools()
    with pytest.raises(InputError, match="VISION_HASH"):
        ground_fact(fact(tools.store.observations[0]), tools, vision=True, image_hash="wrong-hash")


def test_agent_executes_bounded_tools_and_revalidates_cached_proposals(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    tools = api_tools(); valid = proposal([fact(tools.store.observations[0])]); responses = [
        chat(calls=[{"id": "x", "type": "function", "function": {"name": "trace_identity", "arguments": "{}"}}]),
        chat(json.dumps(valid))]
    agent = AuditInvestigator(tmp_path / "dataset", "deepseek", cache=tmp_path / "cache")
    agent.providers["deepseek"] = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test"), agent.ledger,
                                          lambda *args: responses.pop(0))
    baseline = {"issues": [{"code": "NO_DIRECT_STATE"}], "resource_keys": [["account_service", "opaque"]]}
    assert agent.investigate(tools, baseline) == []  # existing fact, no invented new observation
    assert agent.events[-1]["status"] == "LIVE_COMPLETED" and agent.events[-1]["tool_trace"]
    assert agent.events[-1]["accepted"] and agent.ledger.summary()["calls"] == 2
    agent.investigate(tools, baseline)
    assert agent.events[-1]["status"] == "CACHE_HIT" and agent.ledger.summary()["calls"] == 2


def test_agent_skips_genuinely_missing_resource_candidates(tmp_path):
    agent = AuditInvestigator(tmp_path / "dataset", "auto", cache=tmp_path / "cache")
    assert agent.investigate(api_tools(), {"issues": [{"code": "NO_GROUNDED_RESOURCE_LINK"}]}) == []
    assert agent.events[-1]["status"] == "SKIPPED_NO_GROUNDED_RESOURCE_CANDIDATE"


def test_gemini_uses_native_structured_schema_and_local_stricter_validation():
    provider = Provider(ProviderConfig("gemini", "gemini-3.5-flash-lite", "unit-test"), UsageLedger())
    _, body, _ = provider._request([{"role": "user", "content": "Return JSON"}], None, PROPOSAL_SCHEMA)
    config = body["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseSchema"]["type"] == "OBJECT"
    assert config["responseSchema"]["properties"]["facts"]["items"]["type"] == "OBJECT"
    assert "responseJsonSchema" not in config
    invalid = proposal(); invalid["extra"] = True
    with pytest.raises(InputError): validate_json(invalid, PROPOSAL_SCHEMA)


def test_usage_journal_records_reservation_before_transport_and_final_usage(tmp_path):
    ledger = UsageLedger(journal=tmp_path / "usage.jsonl")
    def transport(*args):
        entries = [json.loads(line) for line in ledger.journal.read_text().splitlines()]
        assert entries[-1]["stage"] == "reserved"
        assert not entries[-1]["record"]["usage_reported"]
        return chat("{}")
    provider = Provider(ProviderConfig("deepseek", "deepseek-flash", "never-journal-this-key", .3, 1.2), ledger, transport)
    provider.complete([{"role": "user", "content": "Inspect"}])
    entries = [json.loads(line) for line in ledger.journal.read_text().splitlines()]
    assert [e["stage"] for e in entries] == ["reserved", "completed"]
    assert entries[-1]["record"]["input_tokens"] == 100
    assert "never-journal-this-key" not in ledger.journal.read_text()


def test_http_error_diagnostic_redacts_actual_credentials(monkeypatch):
    import io
    import urllib.error
    import urllib.request
    from deletion_audit.providers import http_json
    secret = "secret-test-credential"
    def reject(*args, **kwargs):
        body = json.dumps({"error": {"message": "Rejected Bearer " + secret}}).encode()
        raise urllib.error.HTTPError("https://example.test", 400, "bad", {}, io.BytesIO(body))
    monkeypatch.setattr(urllib.request, "urlopen", reject)
    with pytest.raises(ProviderError) as caught:
        http_json("https://example.test", {}, {"Authorization": "Bearer " + secret}, 1)
    assert secret not in caught.value.detail and "[REDACTED]" in caught.value.detail


def test_unreported_usage_reserves_cost_instead_of_claiming_free_call():
    ledger = UsageLedger(max_calls=1, max_cost_usd=.1)
    response = chat("{}"); response.pop("usage")
    provider = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test", .3, 1.2), ledger, lambda *args: response)
    provider.complete([{"role": "user", "content": "Inspect"}])
    summary = ledger.summary()
    assert summary["usage_missing_calls"] == 1 and summary["estimated_cost_usd"] > 0


def test_missing_credentials_isolated_without_transport(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    agent = AuditInvestigator(tmp_path / "dataset", "deepseek", cache=tmp_path / "cache")
    agent.providers["deepseek"] = Provider(ProviderConfig("deepseek", "deepseek-flash", ""), agent.ledger,
                                          lambda *args: pytest.fail("Missing key must not send a request"))
    assert agent.investigate(api_tools(), {"issues": [{"code": "NO_DIRECT_STATE"}], "resource_keys": [["account_service", "opaque"]]}) == []
    assert agent.events[-1]["status"] == "CREDENTIAL_UNAVAILABLE" and agent.ledger.summary()["calls"] == 0


def test_malformed_final_proposal_preserved_and_does_not_change_case(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    agent = AuditInvestigator(tmp_path / "dataset", "deepseek", cache=tmp_path / "cache", max_rounds=1)
    agent.providers["deepseek"] = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test"), agent.ledger,
                                          lambda *args: chat("{broken"))
    assert agent.investigate(api_tools(), {"issues": [{"code": "NO_DIRECT_STATE"}], "resource_keys": [["account_service", "opaque"]]}) == []
    assert agent.events[-1]["status"] == "INVESTIGATION_FAILED"
    assert agent.events[-1]["rejected_responses"][0]["response_text"] == "{broken"


def test_invalid_provider_routing_rejected_before_any_model_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_TEXT_PROVIDER", "invented")
    with pytest.raises(InputError, match="route"):
        AuditInvestigator(tmp_path / "dataset", "auto", cache=tmp_path / "cache")


def test_vision_original_image_request_and_validated_cache(tmp_path, monkeypatch):
    import hashlib
    monkeypatch.setenv("LLM_ENABLED", "true")
    dataset = tmp_path / "dataset"
    image = dataset / "evidence/images/screen.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"mock-original-png")  # Mock transport; never decoded as a real raster.
    tools = api_tools()
    fields = {"user_id": "user_fixture", "email": "person@example.test"}
    source = replace(tools.store.observations[0], collection="screen_readback", fields=fields,
                     provenance={"sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                                 "file_path": "evidence/images/screen.png", "raw": fields})
    tools.store.observations[0] = source
    value = fact(source); value.update(interpretation="EXTRACT_VISIBLE", attributes={"email": "person@example.test"})
    result = proposal([value])
    def transport(url, body, headers, timeout):
        assert body["contents"][-1]["parts"][-1]["inlineData"]["mimeType"] == "image/png"
        assert body["generationConfig"]["responseSchema"]["type"] == "OBJECT"
        return {"candidates": [{"content": {"parts": [{"text": json.dumps(result)}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20}}
    agent = AuditInvestigator(dataset, "gemini", cache=tmp_path / "cache")
    agent.providers["gemini"] = Provider(ProviderConfig("gemini", "gemini-3.5-flash-lite", "unit-test"), agent.ledger, transport)
    updates = agent.vision(tools, source.file_id)
    assert len(updates) == 1 and updates[0].observation_id == source.observation_id
    assert updates[0].scope["vision_corroborated"]  # metadata reaches the case-local solver copy
    assert agent.events[-1]["accepted"][0]["enrichment"] and not agent.events[-1]["accepted"][0]["new_fact"]
    assert agent.events[-1]["status"] == "LIVE_COMPLETED" and agent.events[-1]["accepted"]
    agent.vision(tools, source.file_id)
    assert agent.events[-1]["status"] == "CACHE_HIT" and agent.ledger.summary()["calls"] == 1


def test_proposal_cannot_backfill_future_capture_with_past_event_time():
    tools = api_tools()
    source = replace(tools.store.observations[0], captured_at=AT.replace(year=2030))
    tools.store.observations[0] = source
    with pytest.raises(InputError, match="AFTER_CUTOFF"):
        ground_fact(fact(source), tools)
