"""
Deterministyczny solver DC (minimalny zakres v1) dla obwodów rezystancyjnych.

Zakres:
- resistor
- voltage_source
- current_source
"""

from __future__ import annotations

from dataclasses import dataclass

from core.circuit.models import CircuitInput, Element

SUPPORTED_KINDS = {"resistor", "voltage_source", "current_source"}


@dataclass(frozen=True)
class TargetResult:
    element_id: str
    target_type: str
    value: float
    unit: str


@dataclass(frozen=True)
class EquivalentSourceResult:
    node_voltages: dict[str, float]
    element_currents: dict[str, float]
    element_powers: dict[str, float]
    targets: list[TargetResult]


def solve_equivalent_source(circuit: CircuitInput) -> EquivalentSourceResult:
    _validate_supported_elements(circuit.elements)

    voltage_sources = [el for el in circuit.elements if el.kind == "voltage_source"]
    non_ground_nodes = [node for node in circuit.nodes if node != "gnd"]
    node_index = {node: idx for idx, node in enumerate(non_ground_nodes)}
    source_index = {el.id: idx for idx, el in enumerate(voltage_sources)}

    unknown_count = len(non_ground_nodes) + len(voltage_sources)
    if unknown_count == 0:
        return EquivalentSourceResult(
            node_voltages={"gnd": 0.0},
            element_currents={},
            element_powers={},
            targets=[],
        )

    matrix = [[0.0 for _ in range(unknown_count)] for _ in range(unknown_count)]
    rhs = [0.0 for _ in range(unknown_count)]

    for element in circuit.elements:
        if element.kind == "resistor":
            _stamp_resistor(matrix, node_index, element)
        elif element.kind == "current_source":
            _stamp_current_source(rhs, node_index, element)
        elif element.kind == "voltage_source":
            _stamp_voltage_source(matrix, rhs, node_index, source_index, len(non_ground_nodes), element)

    solution = _solve_linear_system(matrix, rhs)

    node_voltages = {"gnd": 0.0}
    for node, idx in node_index.items():
        node_voltages[node] = solution[idx]

    voltage_source_currents = {
        source.id: solution[len(non_ground_nodes) + source_index[source.id]] for source in voltage_sources
    }

    element_currents: dict[str, float] = {}
    element_powers: dict[str, float] = {}

    for element in circuit.elements:
        voltage = node_voltages[element.node_from] - node_voltages[element.node_to]
        if element.kind == "resistor":
            current = voltage / element.value
        elif element.kind == "current_source":
            current = element.value
        else:
            current = voltage_source_currents[element.id]

        element_currents[element.id] = current
        element_powers[element.id] = voltage * current

    targets = _compute_targets(circuit, node_voltages, element_currents, element_powers)

    return EquivalentSourceResult(
        node_voltages=node_voltages,
        element_currents=element_currents,
        element_powers=element_powers,
        targets=targets,
    )


def _validate_supported_elements(elements: list[Element]) -> None:
    unsupported = {el.kind for el in elements if el.kind not in SUPPORTED_KINDS}
    if unsupported:
        unsupported_kinds = ", ".join(sorted(unsupported))
        raise ValueError(f"Unsupported element kind(s) for equivalent source solver: {unsupported_kinds}")


def _stamp_resistor(matrix: list[list[float]], node_index: dict[str, int], element: Element) -> None:
    conductance = 1.0 / element.value
    n_from = node_index.get(element.node_from)
    n_to = node_index.get(element.node_to)

    if n_from is not None:
        matrix[n_from][n_from] += conductance
    if n_to is not None:
        matrix[n_to][n_to] += conductance
    if n_from is not None and n_to is not None:
        matrix[n_from][n_to] -= conductance
        matrix[n_to][n_from] -= conductance


def _stamp_current_source(rhs: list[float], node_index: dict[str, int], element: Element) -> None:
    n_from = node_index.get(element.node_from)
    n_to = node_index.get(element.node_to)

    # Dodatni prąd płynie z node_from do node_to.
    if n_from is not None:
        rhs[n_from] -= element.value
    if n_to is not None:
        rhs[n_to] += element.value


def _stamp_voltage_source(
    matrix: list[list[float]],
    rhs: list[float],
    node_index: dict[str, int],
    source_index: dict[str, int],
    node_unknowns: int,
    element: Element,
) -> None:
    n_from = node_index.get(element.node_from)
    n_to = node_index.get(element.node_to)
    src_col = node_unknowns + source_index[element.id]

    if n_from is not None:
        matrix[n_from][src_col] += 1.0
    if n_to is not None:
        matrix[n_to][src_col] -= 1.0

    if n_from is not None:
        matrix[src_col][n_from] += 1.0
    if n_to is not None:
        matrix[src_col][n_to] -= 1.0

    rhs[src_col] = element.value


def _compute_targets(
    circuit: CircuitInput,
    node_voltages: dict[str, float],
    element_currents: dict[str, float],
    element_powers: dict[str, float],
) -> list[TargetResult]:
    by_id = {el.id: el for el in circuit.elements}
    targets: list[TargetResult] = []

    for target in circuit.targets:
        element = by_id[target.element_id]
        if target.target_type == "voltage":
            value = node_voltages[element.node_from] - node_voltages[element.node_to]
            unit = "V"
        elif target.target_type == "current":
            value = element_currents[element.id]
            unit = "A"
        else:
            value = element_powers[element.id]
            unit = "W"

        targets.append(
            TargetResult(
                element_id=target.element_id,
                target_type=target.target_type,
                value=value,
                unit=unit,
            )
        )

    return targets


def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    size = len(rhs)
    augmented = [row[:] + [rhs_val] for row, rhs_val in zip(matrix, rhs, strict=True)]
    eps = 1e-12

    for pivot_col in range(size):
        pivot_row = max(range(pivot_col, size), key=lambda row: abs(augmented[row][pivot_col]))
        if abs(augmented[pivot_row][pivot_col]) <= eps:
            raise ValueError("Singular circuit matrix; no stable DC solution.")

        if pivot_row != pivot_col:
            augmented[pivot_col], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_col]

        pivot_value = augmented[pivot_col][pivot_col]
        for col in range(pivot_col, size + 1):
            augmented[pivot_col][col] /= pivot_value

        for row in range(size):
            if row == pivot_col:
                continue
            factor = augmented[row][pivot_col]
            if abs(factor) <= eps:
                continue
            for col in range(pivot_col, size + 1):
                augmented[row][col] -= factor * augmented[pivot_col][col]

    return [augmented[row][size] for row in range(size)]
