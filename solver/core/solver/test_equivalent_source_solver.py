import pytest

from core.circuit.models import CircuitInput, Element, TargetSpec
from core.solver.equivalent_source import solve_equivalent_source


def test_golden_single_loop_voltage_source_and_resistor():
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=12.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=6.0),
        ],
    )

    result = solve_equivalent_source(circuit)

    assert result.node_voltages["n1"] == pytest.approx(12.0)
    assert result.element_currents["R1"] == pytest.approx(2.0)
    assert result.element_currents["V1"] == pytest.approx(-2.0)
    assert result.element_powers["R1"] == pytest.approx(24.0)
    assert result.element_powers["V1"] == pytest.approx(-24.0)


def test_golden_voltage_divider_two_mesh_reference_case():
    circuit = CircuitInput(
        nodes=["gnd", "n1", "n2"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=10.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=1000.0),
            Element(id="R2", kind="resistor", node_from="n2", node_to="gnd", value=1000.0),
        ],
        targets=[
            TargetSpec(element_id="R2", target_type="voltage"),
            TargetSpec(element_id="R1", target_type="current"),
        ],
    )

    result = solve_equivalent_source(circuit)

    assert result.node_voltages["n1"] == pytest.approx(10.0)
    assert result.node_voltages["n2"] == pytest.approx(5.0)
    assert result.element_currents["R1"] == pytest.approx(0.005)
    assert result.element_currents["R2"] == pytest.approx(0.005)

    assert len(result.targets) == 2
    assert result.targets[0].unit == "V"
    assert result.targets[0].value == pytest.approx(5.0)
    assert result.targets[1].unit == "A"
    assert result.targets[1].value == pytest.approx(0.005)


def test_golden_current_source_with_parallel_resistors():
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[
            Element(id="I1", kind="current_source", node_from="gnd", node_to="n1", value=3.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=2.0),
            Element(id="R2", kind="resistor", node_from="n1", node_to="gnd", value=4.0),
        ],
    )

    result = solve_equivalent_source(circuit)

    assert result.node_voltages["n1"] == pytest.approx(4.0)
    assert result.element_currents["R1"] == pytest.approx(2.0)
    assert result.element_currents["R2"] == pytest.approx(1.0)
    assert result.element_currents["I1"] == pytest.approx(3.0)


def test_golden_mixed_sources_and_resistors():
    circuit = CircuitInput(
        nodes=["gnd", "n1", "n2"],
        elements=[
            Element(id="V1", kind="voltage_source", node_from="n1", node_to="gnd", value=8.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="n2", value=4.0),
            Element(id="R2", kind="resistor", node_from="n2", node_to="gnd", value=2.0),
            Element(id="I1", kind="current_source", node_from="n2", node_to="gnd", value=1.0),
        ],
    )

    result = solve_equivalent_source(circuit)

    assert result.node_voltages["n1"] == pytest.approx(8.0)
    assert result.node_voltages["n2"] == pytest.approx(4.0 / 3.0)
    assert result.element_currents["R1"] == pytest.approx(5.0 / 3.0)
    assert result.element_currents["R2"] == pytest.approx(2.0 / 3.0)
    assert result.element_currents["I1"] == pytest.approx(1.0)


def test_golden_target_power_current_voltage():
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[
            Element(id="I1", kind="current_source", node_from="gnd", node_to="n1", value=2.0),
            Element(id="R1", kind="resistor", node_from="n1", node_to="gnd", value=5.0),
        ],
        targets=[
            TargetSpec(element_id="R1", target_type="voltage"),
            TargetSpec(element_id="R1", target_type="current"),
            TargetSpec(element_id="R1", target_type="power"),
        ],
    )

    result = solve_equivalent_source(circuit)

    assert result.node_voltages["n1"] == pytest.approx(10.0)
    assert [target.unit for target in result.targets] == ["V", "A", "W"]
    assert [target.value for target in result.targets] == pytest.approx([10.0, 2.0, 20.0])


def test_unsupported_element_kind_for_equivalent_source():
    circuit = CircuitInput(
        nodes=["gnd", "n1"],
        elements=[
            Element(id="L1", kind="inductor", node_from="n1", node_to="gnd", value=1.0),
        ],
    )

    with pytest.raises(ValueError, match="Unsupported element kind"):
        solve_equivalent_source(circuit)
