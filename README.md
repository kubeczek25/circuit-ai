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
