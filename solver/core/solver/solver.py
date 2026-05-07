"""
Punkt wejścia solverów. Weryfikuje główny wynik za pomocą czystego MNA.
"""

from core.solver.mna import solve_mna_core


def check_mna_discrepancies(main_result: dict, mna_result: dict, tol: float = 1e-6) -> list[str]:
    """Porównuje wyniki i zwraca listę rozbieżności."""
    discrepancies = []

    # Sprawdzanie węzłów
    for node, v in main_result["nodes"].items():
        v_mna = mna_result["nodes"].get(node, 0.0)
        if abs(v - v_mna) > tol:
            discrepancies.append(f"Węzeł '{node}': {v}V (Main) vs {v_mna}V (MNA)")

    # Sprawdzanie elementów
    for eid, elem in main_result["elements"].items():
        mna_elem = mna_result["elements"].get(eid)
        if mna_elem:
            if abs(elem["v"] - mna_elem["v"]) > tol:
                discrepancies.append(f"Element '{eid}' V: {elem['v']}V vs {mna_elem['v']}V")
            if abs(elem["i"] - mna_elem["i"]) > tol:
                discrepancies.append(f"Element '{eid}' I: {elem['i']}A vs {mna_elem['i']}A")
            if abs(elem["p"] - mna_elem["p"]) > tol:
                discrepancies.append(f"Element '{eid}' P: {elem['p']}W vs {mna_elem['p']}W")

    return discrepancies


def solve_circuit(circuit) -> dict:
    """
    Główna funkcja orkiestrująca (mock).
    Zwraca ustandaryzowany słownik wymuszony kontraktem.
    """
    # 1. Wywołanie (hipotetycznego) solvera głównego (equivalent_source)
    # Dla spójności testów tutaj użyjemy mockowego bezpośredniego wywołania MNA,
    # ale w realnym kodzie odpalałbyś `equivalent_source_solver`.
    main_result = solve_mna_core(circuit)

    # Inicjalizacja struktury diagnostics
    main_result["diagnostics"] = {"mna_check": {"discrepancies": []}}

    # 2. Weryfikacja niezależnym MNA
    if getattr(circuit.options, "verify_with_mna", False):
        mna_result = solve_mna_core(circuit)
        discrepancies = check_mna_discrepancies(main_result, mna_result)
        main_result["diagnostics"]["mna_check"]["discrepancies"] = discrepancies

    return main_result