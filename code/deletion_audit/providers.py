"""Documented HTTP APIs behind one bounded, observable provider interface."""
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from .ai_config import configured
from .parsers import json_loads


class ProviderError(RuntimeError):
    def __init__(self, code, retryable=False, detail=""):
        super().__init__(code)
        self.retryable = retryable
        self.detail = detail


@dataclass
class UsageLedger:
    max_calls: int = 96
    max_cost_usd: float = 1.0
    records: list[dict] = field(default_factory=list)
    cache_hits: int = 0
    journal: Path | None = None

    def checkpoint(self, record, stage):
        """Append before sending and after completion so interruptions remain visible."""
        if self.journal is not None:
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with self.journal.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps({"call_no": len(self.records), "stage": stage,
                                         "record": record}, ensure_ascii=False) + "\n")
                stream.flush()

    def summary(self):
        models = {}
        for record in self.records:
            key = record["provider"] + "/" + record["model"]
            totals = models.setdefault(key, dict(calls=0, errors=0, input_tokens=0, output_tokens=0, estimated_cost_usd=0.0))
            totals["calls"] += 1
            totals["errors"] += int("error" in record)
            for k in ("input_tokens", "output_tokens", "estimated_cost_usd"):
                totals[k] += record.get(k, 0)
        return {"calls": len(self.records), "errors": sum("error" in r for r in self.records),
                "input_tokens": sum(r.get("input_tokens", 0) for r in self.records),
                "output_tokens": sum(r.get("output_tokens", 0) for r in self.records),
                "estimated_cost_usd": sum(r.get("estimated_cost_usd", 0) for r in self.records),
                "usage_missing_calls": sum(not r.get("usage_reported", False) for r in self.records),
                "cache_hits": self.cache_hits, "by_model": models,
                "limits": {"max_calls": self.max_calls, "max_cost_usd": self.max_cost_usd}}

    def reserve(self, config, input_upper):
        worst = (input_upper * config.input_rate + config.max_tokens * config.output_rate) / 1e6
        if len(self.records) >= self.max_calls or self.summary()["estimated_cost_usd"] + worst > self.max_cost_usd:
            raise ProviderError("RUN_BUDGET_EXHAUSTED")
        return worst


def http_json(url, body, headers, timeout):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read(8_000_001)
            if len(payload) > 8_000_000:
                raise ProviderError("RESPONSE_TOO_LARGE")
            return json_loads(payload.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Keep a bounded API diagnostic only after removing all actual auth values.
        detail = ""
        try:
            error = json.loads(exc.read(8192).decode("utf-8")).get("error", {})
            detail = str(error.get("message", "")) if isinstance(error, dict) else ""
            for name, secret in headers.items():
                if name.lower() in {"authorization", "x-goog-api-key"}:
                    detail = detail.replace(secret, "[REDACTED]").replace(secret.removeprefix("Bearer "), "[REDACTED]")
            detail = re.sub(r"(?:AIza[\w-]{20,}|sk-[\w-]{10,})", "[REDACTED]", detail)[:500]
        except (ValueError, OSError):
            pass
        raise ProviderError("HTTP_" + str(exc.code), exc.code in {408, 429, 500, 502, 503, 504}, detail) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProviderError("NETWORK_OR_TIMEOUT", True) from None
    except ValueError:
        raise ProviderError("MALFORMED_PROVIDER_JSON") from None


@dataclass
class Reply:
    text: str
    calls: list[dict]
    assistant: dict
    usage: dict


class Provider:
    def __init__(self, config, ledger, transport=http_json):
        self.config, self.ledger, self.transport = config, ledger, transport

    def list_models(self):
        if not configured(self.config.key):
            return {"available": False, "error": "CREDENTIAL_UNAVAILABLE", "models": []}
        if self.config.provider == "gemini":
            data = self.transport("https://generativelanguage.googleapis.com/v1beta/models", None,
                                  {"x-goog-api-key": self.config.key}, self.config.timeout)
            return {"available": True, "models": [r["name"].removeprefix("models/") for r in data.get("models", [])]}
        data = self.transport("https://api.deepseek.com/models", None,
                              {"Authorization": "Bearer " + self.config.key}, self.config.timeout)
        return {"available": True, "models": [r["id"] for r in data.get("data", [])]}

    def _request(self, messages, tools, schema, image=None):
        cfg = self.config
        if cfg.provider == "deepseek":
            if image is not None:
                raise ProviderError("VISION_REQUIRES_GEMINI_ROUTE")
            body = {"model": cfg.model, "messages": [{k: v for k, v in m.items() if not k.startswith("_")} for m in messages],
                    "max_tokens": cfg.max_tokens, "temperature": 0, "thinking": {"type": "disabled"}}
            if tools:
                body["tools"] = [{"type": "function", "function": {"name": t["name"], "parameters": t["parameters"]}} for t in tools]
            if schema:
                body["response_format"] = {"type": "json_object"}
            return "https://api.deepseek.com/chat/completions", body, {"Authorization": "Bearer " + cfg.key}
        contents = []
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        for m in messages:
            if m["role"] == "system":
                continue
            if m["role"] == "assistant":
                parts = m.get("_gemini_parts") or [{"text": m.get("content") or ""}]
                role = "model"
            elif m["role"] == "tool":
                parts = [{"functionResponse": {"name": m["name"], "response": json_loads(m["content"])}}]
                role = "user"
            else:
                parts, role = [{"text": m["content"]}], "user"
            contents.append({"role": role, "parts": parts})
        if image:
            contents[-1]["parts"].append({"inlineData": {"mimeType": "image/png", "data": image}})
        generation = {"temperature": 0, "maxOutputTokens": cfg.max_tokens}
        if cfg.model.startswith("gemini-3"):
            generation["thinkingConfig"] = {"thinkingLevel": "LOW"}
        if schema:
            # generateContent uses the documented OpenAPI Schema subset. Keep
            # additionalProperties/length checks in independent local validation.
            def native_schema(node):
                result = {"type": node["type"].upper()}
                if "properties" in node:
                    result["properties"] = {k: native_schema(v) for k, v in node["properties"].items()}
                for key in ("required", "enum"):
                    if node.get(key):
                        result[key] = node[key]
                if "items" in node:
                    result["items"] = native_schema(node["items"])
                return result
            generation.update(responseMimeType="application/json", responseSchema=native_schema(schema))
        body = {"contents": contents, "systemInstruction": {"parts": [{"text": system}]}, "generationConfig": generation}
        if tools:
            body["tools"] = [{"functionDeclarations": [{"name": t["name"], "parametersJsonSchema": t["parameters"]} for t in tools]}]
        from urllib.parse import quote
        return ("https://generativelanguage.googleapis.com/v1beta/models/" + quote(cfg.model, safe="-._") + ":generateContent",
                body, {"x-goog-api-key": cfg.key})

    def complete(self, messages, tools=None, schema=None, image=None, deadline=None, case_id=None):
        cfg = self.config
        if not configured(cfg.key):
            raise ProviderError("CREDENTIAL_UNAVAILABLE")
        url, body, headers = self._request(messages, tools, schema, image)
        input_upper = len(json.dumps(body, ensure_ascii=False).encode("utf-8")) if image is None else 20000
        if input_upper > 100000:
            raise ProviderError("INPUT_BUDGET_EXHAUSTED")
        for attempt in range(cfg.retries + 1):
            if deadline is not None and time.monotonic() >= deadline:
                raise ProviderError("CASE_DEADLINE_EXCEEDED")
            reserved = self.ledger.reserve(cfg, input_upper)
            record = {"provider": cfg.provider, "model": cfg.model, "case_id": case_id, "attempt": attempt,
                      "input_rate_usd_per_million": cfg.input_rate, "output_rate_usd_per_million": cfg.output_rate,
                      "estimated_cost_usd": reserved, "usage_reported": False}
            self.ledger.records.append(record)
            self.ledger.checkpoint(record, "reserved")
            start = time.monotonic()
            try:
                raw = self.transport(url, body, headers, min(cfg.timeout, max(.1, deadline - start)) if deadline else cfg.timeout)
                reply = self._normalize(raw)
                usage = reply.usage
                record.update(input_tokens=usage.get("input_tokens", 0), output_tokens=usage.get("output_tokens", 0),
                              usage_reported=bool(usage), returned_model=raw.get("modelVersion", raw.get("model", cfg.model)))
                if usage:
                    record["estimated_cost_usd"] = (record["input_tokens"] * cfg.input_rate + record["output_tokens"] * cfg.output_rate) / 1e6
                record["latency_seconds"] = time.monotonic() - start
                self.ledger.checkpoint(record, "completed")
                return reply
            except ProviderError as exc:
                record.update(error=str(exc), latency_seconds=time.monotonic() - start)
                if exc.detail:
                    record["error_detail"] = exc.detail
                self.ledger.checkpoint(record, "failed")
                if not exc.retryable or attempt == cfg.retries:
                    raise
                delay = min(2 ** attempt, 4)
                if deadline and time.monotonic() + delay >= deadline:
                    raise
                time.sleep(delay)
            except (KeyError, TypeError, ValueError, IndexError):
                record.update(error="INVALID_RESPONSE_SHAPE", latency_seconds=time.monotonic() - start)
                self.ledger.checkpoint(record, "failed")
                raise ProviderError("INVALID_RESPONSE_SHAPE") from None

    def _normalize(self, data):
        if self.config.provider == "deepseek":
            message = data["choices"][0]["message"]
            calls = [{"id": c["id"], "name": c["function"]["name"], "arguments": json_loads(c["function"]["arguments"])}
                     for c in message.get("tool_calls", [])]
            assistant = {k: message[k] for k in ("role", "content", "tool_calls") if k in message}
            usage = data.get("usage", {})
            normalized = {"input_tokens": usage["prompt_tokens"], "output_tokens": usage["completion_tokens"]} if usage else {}
            return Reply(message.get("content") or "", calls, assistant, normalized)
        parts = data["candidates"][0]["content"]["parts"]
        calls = [{"id": p["functionCall"].get("id", "call_" + str(i)), "name": p["functionCall"]["name"],
                  "arguments": p["functionCall"].get("args", {})} for i, p in enumerate(parts) if "functionCall" in p]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        usage = data.get("usageMetadata", {})
        normalized = {"input_tokens": usage.get("promptTokenCount", 0),
                      "output_tokens": usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)} if usage else {}
        return Reply(text, calls, {"role": "assistant", "content": text, "_gemini_parts": parts}, normalized)
