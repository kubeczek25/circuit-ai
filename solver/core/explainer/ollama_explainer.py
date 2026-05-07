"""
Lokalny adapter wyjaśnień krok-po-kroku oparty o Ollama.

Warstwa jest prezentacyjna: nie liczy obwodu, tylko tłumaczy dostarczony ślad.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.circuit.models import CircuitInput
from core.solver.equivalent_source import EquivalentSourceResult


@dataclass(frozen=True)
class ExplanationStep:
    krok: str
    uzasadnienie: str
    powiazane_elementy: list[str]


@dataclass(frozen=True)
class ExplanationResult:
    status: str
    source: str
    steps: list[ExplanationStep]
    error_code: str | None = None


def generate_ollama_explanation(
    circuit: CircuitInput,
    solver_result: EquivalentSourceResult,
    step_trace: list[str],
    *,
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    timeout_seconds: float = 8.0,
) -> ExplanationResult:
    prompt = _build_prompt(circuit, solver_result, step_trace)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
        },
    }
    endpoint = f"{base_url.rstrip('/')}/api/generate"

    try:
        response_data = _post_json(endpoint, payload, timeout_seconds=timeout_seconds)
        response_text = str(response_data.get("response", "")).strip()
        return _parse_response(response_text)
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return ExplanationResult(
            status="explanation_unavailable",
            source="fallback",
            steps=[],
            error_code="OLLAMA_UNAVAILABLE",
        )


def _build_prompt(circuit: CircuitInput, solver_result: EquivalentSourceResult, step_trace: list[str]) -> str:
    circuit_payload = {
        "nodes": circuit.nodes,
        "elements": [
            {
                "id": element.id,
                "kind": element.kind,
                "node_from": element.node_from,
                "node_to": element.node_to,
                "value": element.value,
            }
            for element in circuit.elements
        ],
    }

    solver_payload = {
        "node_voltages": solver_result.node_voltages,
        "element_currents": solver_result.element_currents,
        "element_powers": solver_result.element_powers,
    }

    return (
        "Jestes asystentem edukacyjnym. Nie liczysz obwodu od zera i nie zmieniasz wynikow.\n"
        "Wyjasniasz wyłącznie na podstawie dostarczonego sladu i wynikow solvera.\n"
        "Zwracaj TYLKO poprawny JSON o schemacie:\n"
        '{"steps":[{"krok":"...","uzasadnienie":"...","powiazane_elementy":["R1","V1"]}]}\n'
        "Kontekst wejscia:\n"
        f"{json.dumps(circuit_payload, ensure_ascii=True)}\n"
        "Wyniki solvera:\n"
        f"{json.dumps(solver_payload, ensure_ascii=True)}\n"
        "Slad obliczen:\n"
        f"{json.dumps(step_trace, ensure_ascii=True)}\n"
    )


def _post_json(url: str, payload: dict[str, Any], *, timeout_seconds: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url=url, data=body, headers={"Content-Type": "application/json"}, method="POST")

    with urlopen(request, timeout=timeout_seconds) as response:
        content = response.read().decode("utf-8")
        return json.loads(content)


def _parse_response(response_text: str) -> ExplanationResult:
    raw = json.loads(response_text)
    raw_steps = raw.get("steps", [])
    steps = [
        ExplanationStep(
            krok=str(step.get("krok", "")).strip(),
            uzasadnienie=str(step.get("uzasadnienie", "")).strip(),
            powiazane_elementy=[str(element_id) for element_id in step.get("powiazane_elementy", [])],
        )
        for step in raw_steps
        if isinstance(step, dict)
    ]

    if not steps:
        raise ValueError("Empty explanation steps from model.")

    return ExplanationResult(status="ok", source="ollama", steps=steps)
