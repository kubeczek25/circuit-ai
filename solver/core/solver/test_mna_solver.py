"""
Testy jednostkowe niezależnego solvera MNA.
Sprawdzają precyzję, konwencję pasywną i weryfikator rozbieżności.
"""

import pytest

from core.circuit.models import CircuitInput, Element, SolveOptions
from core.solver.mna import solve_mna_core
from core.solver.solver import check_mna_discrepancies, solve_circuit


def test_mna_voltage_divider():
    """Golden case: Dzielnik napięcia 10V, 4k Ohm, 6k Ohm"""
    circuit = CircuitInput(
        nodes=["gnd", "n1", "n2"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=10.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=4000.0),
            Element(id="R2", kind="resistor", node_from="n2", node_to="gnd", value=6000.0),
        ],
    )
    result = solve_mna_core(circuit)

    # Napięcia na węzłach
    assert result["nodes"]["n1"] == pytest.approx(10.0, rel=1e-6)
    assert result["nodes"]["n2"] == pytest.approx(6.0, rel=1e-6)

    # Konwencja znaków źródła napięcia (dostarcza 10mW mocy)
    v1 = result["elements"]["V1"]
    assert v1["v"] == pytest.approx(10.0, rel=1e-6)
    assert v1["i"] == pytest.approx(-0.001, rel=1e-6)
    assert v1["p"] == pytest.approx(-0.010, rel=1e-6)

    # Konwencja znaków rezystora 1 (pobiera 4mW)
    r1 = result["elements"]["R1"]
    assert r1["v"] == pytest.approx(4.0, rel=1e-6)
    assert r1["i"] == pytest.approx(0.001, rel=1e-6)
    assert r1["p"] == pytest.approx(0.004, rel=1e-6)


def test_mna_simple_current_source():
    """Golden case: Źródło prądowe 2A zasilające rezystor 5 Ohm"""
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[
            Element(id="I1", kind="current_source", node_from="gnd", node_to="n1", value=2.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=5.0),
        ],
    )
    result = solve_mna_core(circuit)

    assert result["nodes"]["n1"] == pytest.approx(10.0, rel=1e-6)

    # Źródło dostarcza 20W mocy. (node_from=gnd, node_to=n1) -> V = 0 - 10 = -10V
    i1 = result["elements"]["I1"]
    assert i1["v"] == pytest.approx(-10.0, rel=1e-6)
    assert i1["i"] == pytest.approx(2.0, rel=1e-6)
    assert i1["p"] == pytest.approx(-20.0, rel=1e-6)


def test_mna_mixed_superposition():
    """Golden case: Układ mieszany (V-source 12V, I-source 3A, dwa R)."""
    circuit = CircuitInput(
        nodes=["gnd", "n1", "n2"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=12.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=2.0),
            Element(id="I1", kind="current_source", node_from="gnd", node_to="n2", value=3.0),
            Element(id="R2", kind="resistor", node_from="n2", node_to="gnd", value=4.0),
        ],
    )
    result = solve_mna_core(circuit)

    # W tym układzie napięcie V_n2 powinno wynosić dokładnie 12V.
    assert result["nodes"]["n1"] == pytest.approx(12.0, rel=1e-6)
    assert result["nodes"]["n2"] == pytest.approx(12.0, rel=1e-6)

    # Przez R1 nie płynie prąd, bo n1 i n2 mają 12V.
    assert result["elements"]["R1"]["i"] == pytest.approx(0.0, abs=1e-9)
    assert result["elements"]["R1"]["p"] == pytest.approx(0.0, abs=1e-9)


def test_cross_check_discrepancies_detected():
    """Weryfikuje, czy różnice powyżej tolerancji są łapane i raportowane."""
    main_fake_result = {
        "nodes": {"gnd": 0.0, "n1": 10.05},  # Błąd 0.05V celowo
        "elements": {
            "R1": {"v": 10.05, "i": 1.0, "p": 10.0},
        },
    }
    mna_fake_result = {
        "nodes": {"gnd": 0.0, "n1": 10.0},
        "elements": {
            "R1": {"v": 10.0, "i": 1.0, "p": 10.0},
        },
    }

    discrepancies = check_mna_discrepancies(main_fake_result, mna_fake_result, tol=1e-2)
    assert len(discrepancies) == 2
    assert any("n1" in msg for msg in discrepancies)
    assert any("R1" in msg and "V:" in msg for msg in discrepancies)


def test_solve_circuit_integration():
    """Testuje, czy obiekt solve_circuit prawidłowo uzupełnia diagnostics."""
    circuit = CircuitInput(
        options=SolveOptions(verify_with_mna=True),
        nodes=["gnd", "n1"],
        elements=[
            Element(id="I1", kind="current_source", node_from="gnd", node_to="n1", value=1.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=10.0),
        ],
    )

    # Normalnie odpalamy bez błędów
    result = solve_circuit(circuit)
    assert "diagnostics" in result
    assert result["diagnostics"]["mna_check"]["discrepancies"] == []
