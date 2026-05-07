import json
from urllib.error import URLError

import pytest

from core.circuit.models import CircuitInput, Element
from core.explainer import ollama_explainer
from core.solver.equivalent_source import solve_equivalent_source


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _sample_circuit() -> CircuitInput:
    return CircuitInput(
        nodes=["gnd", "n1", "n2"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=10.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=1000.0),
            Element(id="R2", kind="resistor", node_from="n2", node_to="gnd", value=1000.0),
        ],
    )


def test_generate_ollama_explanation_success(monkeypatch: pytest.MonkeyPatch):
    circuit = _sample_circuit()
    result = solve_equivalent_source(circuit)

    payload = {
        "response": json.dumps(
            {
                "steps": [
                    {
                        "krok": "Wyznacz punkt pracy",
                        "uzasadnienie": "Dzielnik 1k/1k daje polowe napiecia.",
                        "powiazane_elementy": ["V1", "R1", "R2"],
                    }
                ]
            }
        )
    }

    def fake_urlopen(request, timeout):  # noqa: ANN001
        assert request.full_url.endswith("/api/generate")
        assert timeout == 8.0
        return _FakeResponse(payload)

    monkeypatch.setattr(ollama_explainer, "urlopen", fake_urlopen)

    explanation = ollama_explainer.generate_ollama_explanation(
        circuit,
        result,
        step_trace=["Zastosowano KCL dla n2.", "Rozwiazano rownanie liniowe."],
    )

    assert explanation.status == "ok"
    assert explanation.source == "ollama"
    assert len(explanation.steps) == 1
    assert explanation.steps[0].powiazane_elementy == ["V1", "R1", "R2"]


def test_generate_ollama_explanation_fallback_on_unavailable_model(monkeypatch: pytest.MonkeyPatch):
    circuit = _sample_circuit()
    result = solve_equivalent_source(circuit)

    def fake_urlopen(request, timeout):  # noqa: ANN001
        raise URLError("connection refused")

    monkeypatch.setattr(ollama_explainer, "urlopen", fake_urlopen)

    explanation = ollama_explainer.generate_ollama_explanation(
        circuit,
        result,
        step_trace=["Brak polaczenia z Ollama."],
    )

    assert explanation.status == "explanation_unavailable"
    assert explanation.source == "fallback"
    assert explanation.error_code == "OLLAMA_UNAVAILABLE"
    assert explanation.steps == []


def test_generate_ollama_explanation_fallback_on_invalid_json(monkeypatch: pytest.MonkeyPatch):
    circuit = _sample_circuit()
    result = solve_equivalent_source(circuit)

    payload = {"response": "{not-json}"}

    def fake_urlopen(request, timeout):  # noqa: ANN001
        return _FakeResponse(payload)

    monkeypatch.setattr(ollama_explainer, "urlopen", fake_urlopen)

    explanation = ollama_explainer.generate_ollama_explanation(
        circuit,
        result,
        step_trace=["Model zwrocil niepoprawna odpowiedz."],
    )

    assert explanation.status == "explanation_unavailable"
    assert explanation.source == "fallback"
