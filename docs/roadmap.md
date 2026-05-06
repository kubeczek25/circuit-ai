# Roadmap

## Milestone 1 - Fundamenty modelu i walidacji

- Ustabilizowanie modeli wejściowych obwodu (Pydantic v2).
- Komplet reguł walidacji fizycznej i topologicznej.
- Zestaw testów jednostkowych dla przypadków poprawnych i brzegowych.

## Milestone 2 - Solver equivalent source (Thevenin/Norton)

- Implementacja ścieżki obliczeniowej dla obwodów rezystancyjnych DC.
- Standaryzacja formatu odpowiedzi solvera.
- Scenariusze testowe typu golden cases.

## Milestone 3 - MNA jako warstwa weryfikacyjna

- Implementacja solvera MNA dla cross-checku wyników.
- Tolerancje porównawcze i raportowanie rozbieżności.
- Rozszerzenie testów o przypadki regresyjne.

## Milestone 4 - Warstwa wyjaśnień AI

- Generowanie kroków rozwiązania w języku naturalnym.
- Powiązanie kroków wyjaśnień z konkretnymi elementami obwodu.
- Kontrola jakości odpowiedzi (spójność i poprawność merytoryczna).
