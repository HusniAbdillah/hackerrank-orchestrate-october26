"""Optional provider configuration; credential values are never serialized."""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .inputs import InputError


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        key, value = key.strip(), value.strip()
        if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].strip()
        if key.replace("_", "").isalnum():
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str
    key: str = field(repr=False)
    input_rate: float = 0
    output_rate: float = 0
    timeout: float = 30
    retries: int = 1
    max_tokens: int = 1536

    @classmethod
    def load(cls, provider: str):
        if provider not in {"gemini", "deepseek"}:
            raise InputError("Unsupported investigator provider")
        prefix = provider.upper()
        model = os.environ.get(prefix + "_MODEL", "gemini-3.5-flash-lite" if provider == "gemini" else "deepseek-flash")
        if not re.fullmatch(r"(?:gemini|gemma|deepseek)-[A-Za-z0-9._-]{1,100}", model):
            raise InputError("Invalid provider model identifier")
        key = os.environ.get(prefix + "_API_KEY", "")
        rates = (.30, 2.50) if provider == "gemini" else (.30, 1.20)
        try:
            cfg = cls(provider, model, key,
                float(os.environ.get(prefix + "_INPUT_USD_PER_MILLION", rates[0])),
                float(os.environ.get(prefix + "_OUTPUT_USD_PER_MILLION", rates[1])),
                float(os.environ.get("LLM_TIMEOUT_SECONDS", 30)),
                int(os.environ.get("LLM_MAX_RETRIES", 1)),
                int(os.environ.get("LLM_MAX_TOKENS", 1536)))
        except ValueError as exc:
            raise InputError("Invalid numeric provider configuration") from exc
        if not (0 < cfg.timeout <= 300 and 0 <= cfg.retries <= 5 and 128 <= cfg.max_tokens <= 8192
                and 0 <= cfg.input_rate <= 1000 and 0 <= cfg.output_rate <= 1000):
            raise InputError("Provider configuration exceeds allowed limits")
        return cfg


def configured(key: str) -> bool:
    return bool(key and not key.lower().startswith(("your_", "replace", "placeholder", "example")))
