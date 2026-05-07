"""
Niezależna implementacja Modified Nodal Analysis (MNA) w czystym Pythonie.
Priorytet: 100% poprawności matematycznej dla układów DC steady-state.
"""

from typing import Any


def gauss_solve(A: list[list[float]], b: list[float]) -> list[float]:
    """Prosta eliminacja Gaussa z częściowym wyborem elementu podstawowego (pivoting)."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]

    for i in range(n):
        # Pivoting
        max_el = abs(M[i][i])
        max_row = i
        for k in range(i + 1, n):
            if abs(M[k][i]) > max_el:
                max_el = abs(M[k][i])
                max_row = k
        M[i], M[max_row] = M[max_row], M[i]

        if abs(M[i][i]) < 1e-12:
            raise ValueError("Macierz osobliwa - obwód nie ma unikalnego rozwiązania (np. zwarcie źródeł napięcia).")

        # Eliminacja
        for k in range(i + 1, n):
            factor = -M[k][i] / M[i][i]
            for j in range(i, n + 1):
                if i == j:
                    M[k][j] = 0.0
                else:
                    M[k][j] += factor * M[i][j]

    # Postępowanie odwrotne
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = M[i][n] / M[i][i]
        for k in range(i - 1, -1, -1):
            M[k][n] -= M[k][i] * x[i]

    return x


def solve_mna_core(circuit: Any) -> dict:
    """
    Główna funkcja rozwiązująca obwód metodą MNA.
    Zwraca słownik z wynikami zgodny z kontraktem (napięcia węzłów oraz parametry elementów).
    """
    # 1. Identyfikacja węzłów i źródeł napięcia
    nodes = [n for n in circuit.nodes if n != "gnd"]
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    v_sources = [el for el in circuit.elements if el.kind == "voltage_source"]

    n_nodes = len(nodes)
    n_vsources = len(v_sources)
    matrix_size = n_nodes + n_vsources

    A = [[0.0] * matrix_size for _ in range(matrix_size)]
    Z = [0.0] * matrix_size

    # 2. Stemplowanie macierzy (Stamping)
    for el in circuit.elements:
        n_from_idx = node_to_idx.get(el.node_from)
        n_to_idx = node_to_idx.get(el.node_to)

        if el.kind == "resistor":
            g = 1.0 / el.value
            if n_from_idx is not None:
                A[n_from_idx][n_from_idx] += g
            if n_to_idx is not None:
                A[n_to_idx][n_to_idx] += g
            if n_from_idx is not None and n_to_idx is not None:
                A[n_from_idx][n_to_idx] -= g
                A[n_to_idx][n_from_idx] -= g

        elif el.kind == "current_source":
            # Prąd wypływa z node_from, wpływa do node_to
            if n_from_idx is not None:
                Z[n_from_idx] -= el.value
            if n_to_idx is not None:
                Z[n_to_idx] += el.value

    for v_idx, el in enumerate(v_sources):
        n_from_idx = node_to_idx.get(el.node_from)
        n_to_idx = node_to_idx.get(el.node_to)
        m_idx = n_nodes + v_idx

        # Równanie źródła: V_from - V_to = Value
        if n_from_idx is not None:
            A[m_idx][n_from_idx] = 1.0
            A[n_from_idx][m_idx] = 1.0  # Wkład prądu źródła do KCL
        if n_to_idx is not None:
            A[m_idx][n_to_idx] = -1.0
            A[n_to_idx][m_idx] = -1.0

        Z[m_idx] = el.value

    # 3. Rozwiązanie układu równań
    x = gauss_solve(A, Z)

    # 4. Interpretacja wyników (Konwencja Pasywna)
    node_voltages = {"gnd": 0.0}
    for node, idx in node_to_idx.items():
        node_voltages[node] = x[idx]

    v_source_currents = {}
    for v_idx, el in enumerate(v_sources):
        # Prąd płynący przez źródło od (+) do (-)
        v_source_currents[el.id] = x[n_nodes + v_idx]

    element_results = {}
    for el in circuit.elements:
        v_from = node_voltages[el.node_from]
        v_to = node_voltages[el.node_to]
        v_elem = v_from - v_to

        if el.kind == "resistor":
            i_elem = v_elem / el.value
        elif el.kind == "voltage_source":
            i_elem = v_source_currents[el.id]
        elif el.kind == "current_source":
            i_elem = el.value
        else:
            i_elem = 0.0

        p_elem = v_elem * i_elem

        element_results[el.id] = {
            "v": v_elem,
            "i": i_elem,
            "p": p_elem,
        }

    return {
        "nodes": node_voltages,
        "elements": element_results,
    }