from __future__ import annotations

from core.api.solver_service import solve_circuit_payload


def _valid_payload() -> dict:
    return {
        "meta": {
            "name": "Dzielnik napiecia",
            "description": "V1=10V, R1=1k, R2=1k",
        },
        "options": {
            "preferred_method": "equivalent_source",
            "verify_with_mna": True,
        },
        "nodes": ["gnd", "n1", "n2"],
        "elements": [
            {"id": "V1", "kind": "voltage_source", "node_from": "n1", "node_to": "gnd", "value": 10.0},
            {"id": "R1", "kind": "resistor", "node_from": "n1", "node_to": "n2", "value": 1000.0},
            {"id": "R2", "kind": "resistor", "node_from": "n2", "node_to": "gnd", "value": 1000.0},
        ],
        "targets": [
            {"element_id": "R2", "target_type": "voltage"},
            {"element_id": "R1", "target_type": "current"},
        ],
    }


def test_solver_service_success_response_shape():
    response = solve_circuit_payload(_valid_payload(), include_explanation=False)

    assert response["status"] == "ok"
    assert response["errors"] == []
    assert response["data"]["node_voltages"]["n2"] == 5.0
    assert response["diagnostics"]["method_used"] == "equivalent_source"
    assert response["diagnostics"]["mna_check"]["performed"] is True
    assert "within_tolerance" in response["diagnostics"]["mna_check"]
    assert "tolerance" in response["diagnostics"]["mna_check"]
    assert "discrepancies" in response["diagnostics"]["mna_check"]


def test_solver_service_invalid_input_schema_returns_error():
    bad_payload = _valid_payload()
    bad_payload["nodes"] = ["n1", "n2"]  # brak gnd

    response = solve_circuit_payload(bad_payload, include_explanation=False)

    assert response["status"] == "error"
    assert response["data"] is None
    assert response["errors"][0]["code"] == "INVALID_INPUT_SCHEMA"