"""
Moduł zawierający reguły walidacji biznesowej i topologicznej dla obwodów.
"""

from typing import Protocol


class ElementLike(Protocol):
    id: str
    kind: str
    node_from: str
    node_to: str
    value: float


class CircuitLike(Protocol):
    nodes: list[str]
    elements: list[ElementLike]


def validate_element_value(element: ElementLike) -> ElementLike:
    """
    Waliduje, czy elementy pasywne (R, L, C) mają wartość ściśle dodatnią.
    """
    passive_kinds = {"resistor", "capacitor", "inductor"}
    if element.kind in passive_kinds and element.value <= 0:
        raise ValueError(f"Wartość dla {element.kind} (id: {element.id}) musi być większa od 0.")
    return element


def validate_circuit_topology(circuit: CircuitLike) -> CircuitLike:
    """
    Waliduje poprawność topologiczną całego obwodu:
    - Obecność dokładnie jednego węzła 'gnd'.
    - Unikalność ID elementów.
    - Istnienie węzłów from/to w głównej liście węzłów.
    """
    # 1. Dokładnie jeden węzeł 'gnd'
    gnd_count = circuit.nodes.count("gnd")
    if gnd_count == 0:
        raise ValueError("Obwód musi zawierać węzeł 'gnd'.")
    if gnd_count > 1:
        raise ValueError("Obwód może zawierać tylko jeden węzeł 'gnd'.")

    # 2. Unikalne ID elementów
    element_ids = [el.id for el in circuit.elements]
    if len(element_ids) != len(set(element_ids)):
        duplicates = {eid for eid in element_ids if element_ids.count(eid) > 1}
        raise ValueError(f"ID elementów muszą być unikalne. Znaleziono duplikaty: {duplicates}")

    # 3. Węzły from/to muszą istnieć w liście nodes
    valid_nodes = set(circuit.nodes)
    for el in circuit.elements:
        if el.node_from not in valid_nodes:
            raise ValueError(f"Element {el.id} wskazuje na nieznany węzeł początkowy (node_from): '{el.node_from}'")
        if el.node_to not in valid_nodes:
            raise ValueError(f"Element {el.id} wskazuje na nieznany węzeł końcowy (node_to): '{el.node_to}'")

    return circuit