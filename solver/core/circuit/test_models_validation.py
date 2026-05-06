"""
Testy jednostkowe modeli i walidatorów.
"""

import pytest
from pydantic import ValidationError

from core.circuit.models import CircuitInput, Element, TargetSpec


def test_valid_circuit_minimal():
    """Testuje utworzenie poprawnego, minimalnego obwodu."""
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="gnd", node_to="n1", value=5.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=100.0)
        ]
    )
    assert circuit.nodes == ["gnd", "n1"]
    assert len(circuit.elements) == 2


def test_default_options():
    """Testuje, czy domyślne opcje solvera są poprawnie aplikowane."""
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[Element(id="R1", kind="resistor", node_from="gnd", node_to="n1", value=10.0)]
    )
    assert circuit.options.preferred_method == "equivalent_source"
    assert circuit.options.verify_with_mna is True


def test_negative_resistor_value():
    """Rezystor nie może mieć wartości <= 0."""
    with pytest.raises(ValidationError, match="Wartość dla resistor .* musi być większa od 0"):
        Element(id="R1", kind="resistor", node_from="gnd", node_to="n1", value=-5.0)

    with pytest.raises(ValidationError, match="Wartość dla resistor .* musi być większa od 0"):
        Element(id="R2", kind="resistor", node_from="gnd", node_to="n1", value=0.0)


def test_non_positive_capacitor_and_inductor_values():
    """Kondensator i cewka muszą mieć wartości > 0."""
    with pytest.raises(ValidationError, match="Wartość dla capacitor .* musi być większa od 0"):
        Element(id="C1", kind="capacitor", node_from="gnd", node_to="n1", value=0.0)

    with pytest.raises(ValidationError, match="Wartość dla inductor .* musi być większa od 0"):
        Element(id="L1", kind="inductor", node_from="gnd", node_to="n1", value=-1.0)


def test_negative_voltage_source_allowed():
    """Źródła mogą przyjmować wartości ujemne."""
    el = Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=-12.0)
    assert el.value == -12.0


def test_missing_gnd_node():
    """Obwód musi posiadać węzeł odniesienia 'gnd'."""
    with pytest.raises(ValidationError, match="Obwód musi zawierać węzeł 'gnd'"):
        CircuitInput(
            nodes=["n1", "n2"],
            elements=[Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=10.0)]
        )


def test_duplicate_gnd_node():
    """Zduplikowany węzeł 'gnd' w liście powinien wyrzucić błąd."""
    with pytest.raises(ValidationError, match="tylko jeden węzeł 'gnd'"):
        CircuitInput(
            nodes=["gnd", "n1", "gnd"],
            elements=[Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=10.0)]
        )


def test_duplicate_element_ids():
    """Każdy element musi mieć unikalne ID."""
    with pytest.raises(ValidationError, match="ID elementów muszą być unikalne"):
        CircuitInput(
            nodes=["gnd", "n1"],
            elements=[
                Element(id="R1", kind="resistor", node_from="gnd", node_to="n1", value=10.0),
                Element(id="R1", kind="capacitor", node_from="n1", node_to="gnd", value=5.0)
            ]
        )


def test_unknown_node_from():
    """Węzeł początkowy elementu musi istnieć w liście nodes."""
    with pytest.raises(ValidationError, match="wskazuje na nieznany węzeł początkowy.*unknown_node"):
        CircuitInput(
            nodes=["gnd", "n1"],
            elements=[Element(id="R1", kind="resistor", node_from="unknown_node", node_to="gnd", value=10.0)]
        )


def test_unknown_node_to():
    """Węzeł końcowy elementu musi istnieć w liście nodes."""
    with pytest.raises(ValidationError, match="wskazuje na nieznany węzeł końcowy.*n2"):
        CircuitInput(
            nodes=["gnd", "n1"],
            elements=[Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=10.0)]
        )


def test_target_spec_assignment():
    """Sprawdzenie poprawności przypisania szukanego celu (TargetSpec)."""
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=10.0)],
        targets=[TargetSpec(element_id="R1", target_type="current")]
    )
    assert len(circuit.targets) == 1
    assert circuit.targets[0].element_id == "R1"
    assert circuit.targets[0].target_type == "current"


def test_invalid_target_type():
    """Odrzucenie nieprawidłowego typu celu w TargetSpec."""
    with pytest.raises(ValidationError):
        TargetSpec(element_id="R1", target_type="invalid_type")


def test_default_meta_values():
    """Meta powinno mieć poprawne domyślne wartości."""
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[Element(id="R1", kind="resistor", node_from="gnd", node_to="n1", value=10.0)],
    )
    assert circuit.meta.name == "Untitled Circuit"
    assert circuit.meta.description is None


def test_invalid_element_kind():
    """Nieznany rodzaj elementu powinien zostać odrzucony przez Literal."""
    with pytest.raises(ValidationError):
        Element(id="X1", kind="transformer", node_from="gnd", node_to="n1", value=1.0)  # type: ignore[arg-type]


def test_invalid_preferred_method():
    """Opcja preferred_method powinna akceptować tylko zdefiniowany kontrakt."""
    with pytest.raises(ValidationError):
        CircuitInput(
            nodes=["gnd", "n1"],
            elements=[Element(id="R1", kind="resistor", node_from="gnd", node_to="n1", value=10.0)],
            options={"preferred_method": "super_solver"},
        )