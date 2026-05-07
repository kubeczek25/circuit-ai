"""
Warstwa orkiestracji: walidacja wejscia -> solver -> cross-check -> explainer.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pydantic import ValidationError

from core.circuit.models import CircuitInput
from core.explainer.ollama_explainer import ExplanationResult, generate_ollama_explanation
from core.solver.equivalent_source import EquivalentSourceResult, solve_equivalent_source
from core.solver.mna_crosscheck import run_mna_crosscheck


def solve_circuit_payload(
    payload: dict[str, Any],
    *,
    include_explanation: bool = True,
    step_trace: list[str] | None = None,
) -> dict[str, Any]:
    try:
        circuit = CircuitInput.model_validate(payload)
        result = solve_equivalent_source(circuit)
        cross = run_mna_crosscheck(circuit, result, tolerance=1e-6) if circuit.options.verify_with_mna else None
        explanation = _resolve_explanation(circuit, result, step_trace or []) if include_explanation else None
        return _build_success_response(result, cross, explanation)
    except ValidationError as error:
        return _build_error_response(
            code="INVALID_INPUT_SCHEMA",
            message="Niepoprawna struktura danych wejsciowych.",
            field="input",
            context={"details": error.errors()},
        )
    except ValueError as error:
        message = str(error)
        if "Unsupported element kind" in message:
            code = "UNSUPPORTED_ELEMENT_KIND"
        elif "Singular circuit matrix" in message:
            code = "SOLVER_NUMERICAL_FAILURE"
        else:
            code = "SOLVER_NUMERICAL_FAILURE"
        return _build_error_response(code=code, message=message, field=None, context={})


def _resolve_explanation(
    circuit: CircuitInput,
    result: EquivalentSourceResult,
    step_trace: list[str],
) -> ExplanationResult:
    trace = step_trace or [
        "Zweryfikowano topologie i typy elementow.",
        "Zbudowano uklad rownan liniowych dla DC steady-state.",
        "Rozwiazano niewiadome i wyznaczono prad, napiecie oraz moce elementow.",
    ]
    return generate_ollama_explanation(circuit, result, trace)


def _build_success_response(
    result: EquivalentSourceResult,
    cross: Any,
    explanation: ExplanationResult | None,
) -> dict[str, Any]:
    targets_payload = [
        {
            "element_id": target.element_id,
            "target_type": target.target_type,
            "value": target.value,
            "unit": target.unit,
        }
        for target in result.targets
    ]

    diagnostics: dict[str, Any] = {
        "method_used": "equivalent_source",
        "mna_check": {
            "performed": bool(cross),
        },
    }
    if cross:
        diagnostics["mna_check"]["within_tolerance"] = cross.within_tolerance
        diagnostics["mna_check"]["tolerance"] = cross.tolerance
        diagnostics["mna_check"]["discrepancies"] = [asdict(item) for item in cross.discrepancies]

    if explanation is not None:
        diagnostics["explanation"] = asdict(explanation)

    return {
        "status": "ok",
        "data": {
            "node_voltages": result.node_voltages,
            "element_currents": result.element_currents,
            "element_powers": result.element_powers,
            "targets": targets_payload,
        },
        "diagnostics": diagnostics,
        "errors": [],
    }


def _build_error_response(
    *,
    code: str,
    message: str,
    field: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "error",
        "data": None,
        "diagnostics": {
            "method_used": "equivalent_source",
            "mna_check": {"performed": False},
        },
        "errors": [
            {
                "code": code,
                "message": message,
                "field": field,
                "context": context,
            }
        ],
    }