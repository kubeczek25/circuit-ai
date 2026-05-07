"""
Moduł realizujący niezależny cross-check za pomocą algorytmu MNA.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from core.solver.mna import solve_mna_core


@dataclass
class EquivalentSourceResult:
    """Struktura wspólna do porównań wyników obu algorytmów."""
    node_voltages: Dict[str, float]
    element_currents: Dict[str, float]
    element_powers: Dict[str, float]
    targets: List[Any] = field(default_factory=list)


@dataclass
class MnaDiscrepancy:
    """Reprezentacja pojedynczej rozbieżności."""
    element_id: str
    parameter: str
    expected: float
    actual: float
    difference: float


@dataclass
class MnaCrossCheckResult:
    """Końcowy raport diagnostyczny walidacji."""
    performed: bool
    within_tolerance: bool
    tolerance: float
    discrepancies: List[MnaDiscrepancy] = field(default_factory=list)


def solve_mna(circuit: Any) -> EquivalentSourceResult:
    """
    Rozwiązuje obwód z użyciem natywnego silnika MNA (solve_mna_core).
    Konwertuje surowy dict do postaci używanej przez cross-check.
    Nie odpytuje solvera equivalent_source.
    """
    raw = solve_mna_core(circuit)
    
    return EquivalentSourceResult(
        node_voltages=raw["nodes"],
        element_currents={eid: data["i"] for eid, data in raw["elements"].items()},
        element_powers={eid: data["p"] for eid, data in raw["elements"].items()},
        targets=[]
    )


def run_mna_crosscheck(
    circuit: Any,
    equivalent_result: EquivalentSourceResult,
    *,
    tolerance: float = 1e-6,
) -> MnaCrossCheckResult:
    """Sprawdza różnice między wynikiem głównego algorytmu a wynikiem referencyjnym MNA."""
    try:
        mna_res = solve_mna(circuit)
    except Exception:
        return MnaCrossCheckResult(performed=False, within_tolerance=False, tolerance=tolerance)

    discrepancies = []

    # Walidacja węzłów
    for node, v_main in equivalent_result.node_voltages.items():
        v_mna = mna_res.node_voltages.get(node, 0.0)
        diff = abs(v_main - v_mna)
        if diff > tolerance:
            discrepancies.append(MnaDiscrepancy(node, "node_voltage", v_main, v_mna, diff))

    # Walidacja prądów elementów
    for eid, i_main in equivalent_result.element_currents.items():
        i_mna = mna_res.element_currents.get(eid, 0.0)
        diff = abs(i_main - i_mna)
        if diff > tolerance:
            discrepancies.append(MnaDiscrepancy(eid, "i", i_main, i_mna, diff))

    # Walidacja mocy
    for eid, p_main in equivalent_result.element_powers.items():
        p_mna = mna_res.element_powers.get(eid, 0.0)
        diff = abs(p_main - p_mna)
        if diff > tolerance:
            discrepancies.append(MnaDiscrepancy(eid, "p", p_main, p_mna, diff))

    return MnaCrossCheckResult(
        performed=True,
        within_tolerance=len(discrepancies) == 0,
        tolerance=tolerance,
        discrepancies=discrepancies
    )