"""Independent regressions for source-supported submission debugging fixes."""
from dataclasses import replace

import pytest

from deletion_audit.artifact_links import enrich_artifacts
from deletion_audit.observations import EvidenceStore, identifiers
from deletion_audit.solver import audit, scope_negatives
from deletion_audit.policy import Policy
from deletion_audit.state import exposed, observed_state
from test_solver import ROOT, AT, graph, obs, request


@pytest.mark.parametrize("text", ["Send updates to person@example.test.", "Call +1 555 555 0101."])
def test_literal_contact_in_support_body_is_pii_even_when_columns_null(text):
    assert exposed({"email": None, "phone": None, "message_text": text}) is True


def test_permitted_reference_and_no_visible_contacts_do_not_prove_redaction():
    assert exposed({"subject_reference": "user_fixture", "message_text": "Order dispatched."}) is None
    assert exposed({"subject_reference": "user_fixture", "message_text": "[REDACTED]"}) is False


def test_support_body_readback_overcomes_older_negative_and_has_complete_plan():
    store = EvidenceStore()
    store.add([obs("SUPPORT_MESSAGE", {"subject_reference": "user_fixture",
        "message_text": "Please contact person@example.test about the shared order."}, "ticket", "support_platform")])
    status, steps, diagnostic = audit(request(), store, graph(), Policy.load(ROOT/"dataset"))
    assert status == "INCOMPLETE" and not diagnostic["issues"]
    assert [s["operation"] for s in steps] == ["REPORT_EXPOSED_PII", "REDACT_RECORD", "VERIFY_RECORD_REDACTED"]
    assert all(s["evidence_id"] == "" for s in steps[1:])


def test_mixed_sql_without_declared_service_scope_cannot_prove_other_record_absent():
    known = obs("SECURITY_AUDIT_LOG", {"user_id": "user_fixture"}, "journal", "security_service")
    other = replace(known, resource_id="another_journal", fields={"decoded_record": {"user_id": "user_other"}},
                    scope={"table": "mixed_table", "snapshot_scope": []})
    store = EvidenceStore(); store.add([known, other])
    assert scope_negatives(store, {("security_service", "journal")}, AT) == []


def sources(text, *, attachment=False, late=False):
    reference = "receipt.pdf" if attachment else "STMT-EXAMPLE"
    link_text = ("Attachment catalog confirmed opaque (receipt.pdf) belongs only to person@example.test and user_fixture; no other subject is linked."
                 if attachment else "Data catalog linked opaque (STMT-EXAMPLE) to person@example.test and user_fixture.")
    link = obs(fields={"event_type": "LINK_RESOURCE_IDENTITY", "details": link_text},
               system="object_storage" if attachment else "export_service", kind="reported_claim")
    link = replace(link, source_id="activity_20", observation_id="activity_20", identifiers=identifiers(link.fields),
                   captured_at=AT.replace(year=2030) if late else link.captured_at)
    source = replace(obs(fields={"text": text}), collection="ocr_text" if attachment else "pdf_text",
                     resource_id=None, system_id=None, kind="context", observation_id="document", identifiers=identifiers(text))
    store = EvidenceStore(); store.add([source, link])
    return store


def test_document_catalog_alias_requires_literal_reference_and_same_subject():
    store = sources("CUSTOMER STATEMENT Statement STMT-EXAMPLE person@example.test user_fixture")
    assert enrich_artifacts(store)
    item = store.observations[-1]
    assert item.category == "USER_EXPORT" and observed_state(item) == "PRESENT"
    assert item.scope["catalog_link_id"] == "activity_20" and item.source_id == "evidence_1"
    assert enrich_artifacts(store) == []
    wrong = sources("CUSTOMER STATEMENT Statement STMT-EXAMPLE unrelated@example.test user_other")
    assert enrich_artifacts(wrong) == []


def test_join_cannot_backdate_late_catalog_knowledge():
    store = sources("CUSTOMER STATEMENT Statement STMT-EXAMPLE person@example.test user_fixture", late=True)
    enrich_artifacts(store)
    assert not store.observations[-1].admissible(AT)
    assert store.observations[-1].observed_at < AT  # the underlying document is old


def test_attachment_listing_requires_sole_owner_catalog_and_visible_file_metadata():
    text = "Nimbus Object Storage support-attachments receipt.pdf Version Size application/pdf"
    store = sources(text, attachment=True)
    assert enrich_artifacts(store) and store.observations[-1].fields["shared_attachment"] is False
    unrelated = sources(text.replace("receipt.pdf", "different.pdf"), attachment=True)
    assert enrich_artifacts(unrelated) == []
    incomplete = sources("receipt.pdf", attachment=True)
    assert enrich_artifacts(incomplete) == []
