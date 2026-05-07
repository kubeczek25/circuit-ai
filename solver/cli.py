from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.api.solver_service import solve_circuit_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Circuit AI solver CLI")
    parser.add_argument("--input", required=True, help="Sciezka do pliku JSON z obwodem.")
    parser.add_argument(
        "--no-explanation",
        action="store_true",
        help="Wylacza warstwe explainera (szybsze wykonanie, bez Ollama).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    response = solve_circuit_payload(payload, include_explanation=not args.no_explanation)
    print(json.dumps(response, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
