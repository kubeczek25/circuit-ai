# Decision Log

## 2026-05-06 - Główna ścieżka obliczeń: equivalent source

- **Decyzja:** Domyślną metodą solvera jest podejście equivalent source (Thevenin/Norton).
- **Uzasadnienie:** Dobrze pasuje do prostych obwodów i czytelnego tłumaczenia kroków użytkownikowi.
- **Konsekwencje:** Interfejs opcji solvera utrzymuje tę metodę jako domyślną.

## 2026-05-06 - MNA jako niezależny cross-check

- **Decyzja:** MNA będzie rozwijane jako metoda weryfikacyjna wyników.
- **Uzasadnienie:** Pozwala wykrywać regresje i błędy modeli równoległą ścieżką.
- **Konsekwencje:** W opcjach rozwiązania pozostaje flaga `verify_with_mna`.

## 2026-05-06 - AI jako warstwa wyjaśnień, nie źródło prawdy obliczeń

- **Decyzja:** Komponent AI odpowiada za objaśnienie rozwiązania, nie za same obliczenia.
- **Uzasadnienie:** Rozdzielenie odpowiedzialności zwiększa wiarygodność i testowalność solvera.
- **Konsekwencje:** Rdzeń obliczeniowy pozostaje deterministyczny i testowany klasycznie.
