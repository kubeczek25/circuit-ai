from unittest.mock import patch
from core.solver.mna_crosscheck import (
    EquivalentSourceResult, 
    run_mna_crosscheck, 
    solve_mna
)

class MockCircuit:
    """Pusta zaślepka klasy obwodu do weryfikacji przepływów wywołań."""
    pass

@patch("core.solver.mna_crosscheck.solve_mna_core")
def test_solve_mna_conversion(mock_solve_mna_core):
    """A) Sprawdza użycie niezależnego MNA i poprawność mapowania surowego dict."""
    mock_solve_mna_core.return_value = {
        "nodes": {"gnd": 0.0, "n1": 5.0},
        "elements": {
            "R1": {"v": 5.0, "i": 0.5, "p": 2.5}
        }
    }
    
    circuit = MockCircuit()
    res = solve_mna(circuit)
    
    # Assert poprawności mapowania ściśle według wymagań
    assert res.node_voltages["n1"] == 5.0
    assert res.element_currents["R1"] == 0.5
    assert res.element_powers["R1"] == 2.5
    assert res.targets == []

@patch("core.solver.mna_crosscheck.solve_mna")
def test_run_mna_crosscheck_identifies_differences(mock_solve_mna):
    """B) Sprawdza zachowanie istnejącej funkcji wyłapywania rozbieżności w elementach."""
    mock_solve_mna.return_value = EquivalentSourceResult(
        node_voltages={"n1": 5.0},
        element_currents={"R1": 0.5},
        element_powers={"R1": 2.5},
        targets=[]
    )
    
    main_res = EquivalentSourceResult(
        node_voltages={"n1": 10.0},
        element_currents={"R1": 1.0},
        element_powers={"R1": 10.0},
        targets=[]
    )
    
    report = run_mna_crosscheck(MockCircuit(), main_res, tolerance=1e-6)
    
    assert report.performed is True
    assert report.within_tolerance is False
    assert len(report.discrepancies) == 3 # n1 (voltage), R1 (i), R1 (p)
    assert any(d.element_id == "R1" and d.parameter == "i" and d.difference == 0.5 for d in report.discrepancies)