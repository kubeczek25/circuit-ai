"""
Definicje modeli domenowych dla obwodów elektrycznych.
Korzysta z Pydantic v2 do walidacji typów i struktury.
"""

from typing import Literal
from pydantic import BaseModel, Field, model_validator

from core.circuit.validation import validate_element_value, validate_circuit_topology


class TargetSpec(BaseModel):
    """Specyfikacja szukanego parametru w obwodzie."""
    element_id: str
    target_type: Literal["voltage", "current", "power"]


class CircuitMeta(BaseModel):
    """Metadane obwodu."""
    name: str = "Untitled Circuit"
    description: str | None = None


class SolveOptions(BaseModel):
    """Opcje konfiguracyjne dla algorytmu rozwiązującego."""
    preferred_method: Literal["equivalent_source", "mna"] = "equivalent_source"
    verify_with_mna: bool = True


class Element(BaseModel):
    """Pojedynczy element obwodu (np. rezystor, źródło napięcia)."""
    id: str
    kind: Literal["resistor", "capacitor", "inductor", "voltage_source", "current_source"]
    node_from: str
    node_to: str
    value: float

    @model_validator(mode="after")
    def validate_element(self) -> "Element":
        """Uruchamia zewnętrzną walidację fizycznych właściwości elementu."""
        return validate_element_value(self)


class CircuitInput(BaseModel):
    """Główny model wejściowy reprezentujący cały obwód."""
    meta: CircuitMeta = Field(default_factory=CircuitMeta)
    options: SolveOptions = Field(default_factory=SolveOptions)
    nodes: list[str]
    elements: list[Element]
    targets: list[TargetSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_circuit(self) -> "CircuitInput":
        """Uruchamia zewnętrzną walidację topologii całego obwodu."""
        return validate_circuit_topology(self)