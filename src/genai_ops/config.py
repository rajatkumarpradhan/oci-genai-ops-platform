"""Configuration loading for the genai_ops toolkit.

Configuration is plain JSON (a subset of YAML) so the toolkit stays
dependency-free. Every section has safe defaults; unknown keys are
rejected loudly rather than ignored.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

_ALLOWED_TOP = {"pipeline", "retrieval", "generation", "guardrails", "cost", "observability"}
_ALLOWED_SECTION = {
    "pipeline": {"name", "chunk_size", "chunk_overlap", "max_answer_tokens"},
    "retrieval": {"top_k", "vector_weight", "bm25_weight", "min_score"},
    "generation": {"client", "temperature", "require_citations"},
    "guardrails": {"redact_pii", "block_injection", "max_input_chars"},
    "cost": {"monthly_budget_units", "warn_fraction", "input_token_price", "output_token_price"},
    "observability": {"log_level", "emit_traces", "metrics_namespace"},
}


@dataclass
class PipelineConfig:
    name: str = "genai-ops"
    chunk_size: int = 512
    chunk_overlap: int = 64
    max_answer_tokens: int = 512


@dataclass
class RetrievalConfig:
    top_k: int = 4
    vector_weight: float = 0.6
    bm25_weight: float = 0.4
    min_score: float = 0.0


@dataclass
class GenerationConfig:
    client: str = "offline-extractive"
    temperature: float = 0.0
    require_citations: bool = True


@dataclass
class GuardrailsConfig:
    redact_pii: bool = True
    block_injection: bool = True
    max_input_chars: int = 8000


@dataclass
class CostConfig:
    monthly_budget_units: float = 100.0
    warn_fraction: float = 0.8
    input_token_price: float = 0.0015
    output_token_price: float = 0.002


@dataclass
class ObservabilityConfig:
    log_level: str = "INFO"
    emit_traces: bool = True
    metrics_namespace: str = "genai_ops"


@dataclass
class Settings:
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    _SECTION_MAP = {
        "pipeline": PipelineConfig,
        "retrieval": RetrievalConfig,
        "generation": GenerationConfig,
        "guardrails": GuardrailsConfig,
        "cost": CostConfig,
        "observability": ObservabilityConfig,
    }

    @classmethod
    def from_dict(cls, raw: dict) -> "Settings":
        if not isinstance(raw, dict):
            raise ValueError("settings root must be an object")
        unknown = set(raw) - _ALLOWED_TOP
        if unknown:
            raise ValueError(f"unknown config sections: {sorted(unknown)}")
        settings = cls()
        for section, values in raw.items():
            if not isinstance(values, dict):
                raise ValueError(f"section {section!r} must be an object")
            unknown_keys = set(values) - _ALLOWED_SECTION[section]
            if unknown_keys:
                raise ValueError(f"unknown keys in {section}: {sorted(unknown_keys)}")
            dc = getattr(settings, section)
            for key, value in values.items():
                setattr(dc, key, value)
        return settings

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def to_dict(self) -> dict:
        return {
            "pipeline": asdict(self.pipeline),
            "retrieval": asdict(self.retrieval),
            "generation": asdict(self.generation),
            "guardrails": asdict(self.guardrails),
            "cost": asdict(self.cost),
            "observability": asdict(self.observability),
        }
