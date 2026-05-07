# Circuit AI

Circuit AI to projekt do modelowania i rozwiązywania prostych obwodów elektrycznych.
Aktualny etap skupia się na stabilnych fundamentach: modelach danych, walidacji wejścia
oraz testach jednostkowych dla warstwy `solver`.

## Wymagania

- Python 3.12
- `pip` oraz wirtualne środowisko (`venv`)

## Szybki start

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip pytest pydantic
pytest
```

## Aktualny zakres

- Modele domenowe obwodów (`solver/core/circuit/models.py`)
- Reguły walidacji biznesowej i topologicznej (`solver/core/circuit/validation.py`)
- Testy modeli i walidatorów (`solver/core/circuit/test_models_validation.py`)

## Solver contract v1

Kontrakt v1 definiuje stabilny format wejścia/wyjścia dla deterministycznego solvera DC.
Wersja v1 obejmuje tylko obwody rezystancyjne w stanie ustalonym (DC steady-state).

### Zakres v1

- Dozwolone elementy: `resistor`, `voltage_source`, `current_source`
- Metoda domyślna: `equivalent_source`
- Metoda opcjonalna (walidacja): `mna`
- AI nie bierze udziału w obliczeniach liczbowych

### Input (request JSON)

```json
{
  "meta": {
    "name": "string",
    "description": "string|null"
  },
  "options": {
    "preferred_method": "equivalent_source|mna",
    "verify_with_mna": true
  },
  "nodes": ["gnd", "n1", "n2"],
  "elements": [
    {
      "id": "R1",
      "kind": "resistor|voltage_source|current_source",
      "node_from": "n1",
      "node_to": "gnd",
      "value": 1000.0
    }
  ],
  "targets": [
    {
      "element_id": "R1",
      "target_type": "voltage|current|power"
    }
  ]
}
```

Uwagi dla v1:
- `nodes` musi zawierać dokładnie jeden węzeł `gnd`.
- `elements[].id` musi być unikalne.
- `elements[].node_from` i `elements[].node_to` muszą istnieć w `nodes`.
- Dla `resistor` wartość `value` musi być `> 0`.
- Dla źródeł (`voltage_source`, `current_source`) wartość może być dodatnia lub ujemna.
- `targets` jest opcjonalne; gdy puste, solver zwraca komplet wyników dla obwodu.

### Output (response JSON)

```json
{
  "status": "ok",
  "data": {
    "node_voltages": {
      "gnd": 0.0,
      "n1": 10.0,
      "n2": 5.0
    },
    "element_currents": {
      "R1": 0.005,
      "V1": -0.005
    },
    "element_powers": {
      "R1": 0.025,
      "V1": -0.05
    },
    "targets": [
      {
        "element_id": "R1",
        "target_type": "voltage",
        "value": 5.0,
        "unit": "V"
      }
    ]
  },
  "diagnostics": {
    "method_used": "equivalent_source",
    "mna_check": {
      "performed": true,
      "within_tolerance": true,
      "tolerance": 1e-06
    }
  },
  "errors": []
}
```

W przypadku błędu:
- `status` = `error`
- `data` = `null`
- `errors` zawiera listę błędów domenowych

### Błędy domenowe (v1)

Wspólny format błędu:

```json
{
  "code": "string",
  "message": "string",
  "field": "string|null",
  "context": {}
}
```

Minimalny katalog kodów błędów:
- `INVALID_INPUT_SCHEMA` - niepoprawna struktura JSON lub typ danych.
- `UNSUPPORTED_ELEMENT_KIND` - element spoza zakresu v1.
- `MISSING_GND_NODE` - brak węzła `gnd`.
- `MULTIPLE_GND_NODES` - więcej niż jeden węzeł `gnd`.
- `DUPLICATE_ELEMENT_ID` - zduplikowane identyfikatory elementów.
- `UNKNOWN_NODE_REFERENCE` - element wskazuje węzeł spoza listy `nodes`.
- `INVALID_ELEMENT_VALUE` - niedozwolona wartość elementu (np. `resistor <= 0`).
- `UNKNOWN_TARGET_ELEMENT` - `targets[].element_id` nie istnieje w `elements`.
- `UNSUPPORTED_TARGET_TYPE` - niedozwolony typ targetu.
- `SOLVER_NUMERICAL_FAILURE` - solver nie znalazł stabilnego rozwiązania.
- `MNA_CHECK_FAILED` - cross-check MNA wykrył rozbieżność poza tolerancją.

### Przykład poprawnego requestu

```json
{
  "meta": {
    "name": "Dzielnik napięcia",
    "description": "V1=10V, R1=1k, R2=1k"
  },
  "options": {
    "preferred_method": "equivalent_source",
    "verify_with_mna": true
  },
  "nodes": ["gnd", "n1", "n2"],
  "elements": [
    { "id": "V1", "kind": "voltage_source", "node_from": "n1", "node_to": "gnd", "value": 10.0 },
    { "id": "R1", "kind": "resistor", "node_from": "n1", "node_to": "n2", "value": 1000.0 },
    { "id": "R2", "kind": "resistor", "node_from": "n2", "node_to": "gnd", "value": 1000.0 }
  ],
  "targets": [
    { "element_id": "R2", "target_type": "voltage" },
    { "element_id": "R1", "target_type": "current" }
  ]
}
```

### Przykład odpowiedzi błędu

```json
{
  "status": "error",
  "data": null,
  "diagnostics": {
    "method_used": "equivalent_source",
    "mna_check": {
      "performed": false
    }
  },
  "errors": [
    {
      "code": "MISSING_GND_NODE",
      "message": "Obwód musi zawierać węzeł 'gnd'.",
      "field": "nodes",
      "context": {}
    }
  ]
}
```

## Definition of Done (task-a-spec)

Task `task-a-spec` uznaje się za ukończony, gdy:
- Kontrakt v1 jest opisany w `README.md` (zakres, I/O, błędy, przykłady).
- Format wejścia i wyjścia jest jednoznaczny i gotowy do implementacji parsera/serializacji.
- Katalog błędów domenowych ma stabilne kody do użycia w API/CLI.
- Przykład sukcesu i przykład błędu są kompletne i możliwe do wykorzystania jako fixture testowe.
- Kontrakt jest spójny z kierunkiem architektonicznym: `equivalent_source` jako ścieżka główna, `mna` jako cross-check.

## Konwencja znaku prądu i mocy (Pasywna Konwencja Znaków)
Aplikacja `circuit-ai` operuje na standardowej **pasywnej konwencji znaków**:
- Napięcie na elemencie ($V_{elem}$) to zawsze: $V_{from} - V_{to}$.
- Prąd ($I$) uznaje się za dodatni, gdy płynie od węzła `node_from` do `node_to` (wpływa przez biegun dodatni).
- Moc ($P$) elementu to $P = V_{elem} \times I$.
  - Jeśli $P > 0$ — element **pobiera/rozprasza** moc (np. działający rezystor).
  - Jeśli $P < 0$ — element **oddaje/dostarcza** moc do układu (typowe zachowanie poprawnie obciążonych źródeł napięciowych i prądowych).