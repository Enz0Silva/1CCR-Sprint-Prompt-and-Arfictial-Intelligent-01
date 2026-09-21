"""
Mede os tokens de cada versao do system prompt com tiktoken (Aula 04).

Preenche a coluna "Tokens" de prompts/VERSOES.md com valor medido, nao estimado.
Nao chama o modelo — e deterministico e roda offline.

    python evals/medir_prompts.py
    python evals/medir_prompts.py --turnos 10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
    _FONTE = "tiktoken cl100k_base"

    def contar(texto: str) -> int:
        return len(_ENC.encode(texto))

except ImportError:
    _FONTE = "ESTIMATIVA por caracteres (pip install tiktoken para o valor real)"

    def contar(texto: str) -> int:
        return round(len(texto) / 3.6)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--turnos", type=int, default=10,
                    help="Numero de turnos para projetar o custo acumulado")
    args = ap.parse_args()

    versoes = sorted(p.stem.replace("system_prompt_", "")
                     for p in config.PROMPTS_DIR.glob("system_prompt_*.md"))
    if not versoes:
        sys.exit(f"Nenhum system_prompt_*.md em {config.PROMPTS_DIR}")

    medidas = {v: contar(config.carregar_system_prompt(v)) for v in versoes}
    base = medidas[versoes[0]]

    print(f"Fonte da contagem: {_FONTE}")
    print(f"O system prompt entra em TODOS os turnos — custo projetado para "
          f"{args.turnos} turnos.\n")
    print("| Versao | Tokens | vs v1 | Custo em " + str(args.turnos) + " turnos |")
    print("|--------|--------|-------|----------------|")
    for v in versoes:
        t = medidas[v]
        delta = "baseline" if t == base else f"{(t / base - 1) * 100:+.0f}%"
        print(f"| {v} | {t} | {delta} | {t * args.turnos} |")

    print("\nCole a coluna 'Tokens' em prompts/VERSOES.md.")


if __name__ == "__main__":
    main()
