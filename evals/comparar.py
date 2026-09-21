"""
Gera a tabela antes/depois em Markdown a partir de evals/sprint3_results.json.

Essa tabela e a evidencia central do refactory (§8 do enunciado). Sem ela, o
bloco D da rubrica perde a maior parte dos pontos.

Uso:
    python evals/run_eval.py --alvo legado --tag sprint2
    python evals/run_eval.py --alvo lcel   --tag sprint3
    python evals/comparar.py --antes sprint2 --depois sprint3
    python evals/comparar.py --tags v1 v2 v3      # comparativo de prompts
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config

RESULTS = config.RAIZ / "evals" / "sprint3_results.json"

LINHAS = [
    ("Qualidade das respostas (nota 0-10 no eval)", "nota_0_10", "{:.2f}", "maior"),
    ("Score ponderado (0-1)", "score_ponderado", "{:.3f}", "maior"),
    ("Comportamento esperado (% dos casos)", "comportamento_ok_pct", "{:.1f}%", "maior"),
    ("Tokens por turno (media)", "tokens_medio_por_turno", "{:.0f}", "menor"),
    ("Latencia media (s)", "latencia_media_s", "{:.2f}", "menor"),
    ("Acuracia do structured output (%)", "acuracia_structured_output_pct", "{:.1f}%", "maior"),
]


def carregar() -> dict:
    if not RESULTS.exists():
        sys.exit(f"{RESULTS} nao existe. Rode evals/run_eval.py primeiro.")
    return json.loads(RESULTS.read_text(encoding="utf-8"))


def variacao(antes: float, depois: float, direcao: str) -> str:
    if antes in (0, None):
        return "n/a" if depois in (0, None) else "novo"
    delta = (depois - antes) / abs(antes) * 100
    sinal = "+" if delta >= 0 else ""
    melhorou = (delta > 0) if direcao == "maior" else (delta < 0)
    marca = "melhor" if melhorou else "pior"
    if abs(delta) < 1:
        marca = "estavel"
    return f"{sinal}{delta:.1f}% ({marca})"


def tabela_antes_depois(dados: dict, tag_antes: str, tag_depois: str) -> str:
    for t in (tag_antes, tag_depois):
        if t not in dados:
            sys.exit(f"Tag '{t}' ausente. Disponiveis: {sorted(dados)}")

    a, d = dados[tag_antes]["resumo"], dados[tag_depois]["resumo"]
    ma, md = dados[tag_antes], dados[tag_depois]

    out = [
        f"### Comparativo antes/depois — {tag_antes} x {tag_depois}",
        "",
        f"Modelo: `{md['modelo']}` | prompt antes: `{ma['prompt']}` | "
        f"prompt depois: `{md['prompt']}` | execucao: {md['executado_em']}",
        "",
        "| Metrica | Sprints 1/2 (manual/legado) | Sprint 03 (LCEL) | Variacao |",
        "|---------|------------------------------|------------------|----------|",
    ]
    for rotulo, chave, fmt, direcao in LINHAS:
        va, vd = a.get(chave, 0), d.get(chave, 0)
        out.append(f"| {rotulo} | {fmt.format(va)} | {fmt.format(vd)} | "
                   f"{variacao(va, vd, direcao)} |")

    out += ["", "#### Score por categoria de caso", "",
            "| Categoria | Antes | Depois |", "|-----------|-------|--------|"]
    categorias = sorted(set(a.get("score_por_categoria", {})) |
                        set(d.get("score_por_categoria", {})))
    for cat in categorias:
        out.append(f"| {cat} | {a.get('score_por_categoria', {}).get(cat, 0):.2f} | "
                   f"{d.get('score_por_categoria', {}).get(cat, 0):.2f} |")

    # Casos que viraram o jogo
    ra = {r["id"]: r for r in dados[tag_antes]["resultados"]}
    rd = {r["id"]: r for r in dados[tag_depois]["resultados"]}
    viradas = [(i, ra[i]["score"], rd[i]["score"]) for i in ra
               if i in rd and abs(rd[i]["score"] - ra[i]["score"]) >= 0.3]
    if viradas:
        out += ["", "#### Casos com maior variacao", "",
                "| Caso | Antes | Depois |", "|------|-------|--------|"]
        for cid, sa, sd in sorted(viradas, key=lambda x: x[2] - x[1], reverse=True):
            out.append(f"| {cid} | {sa:.2f} | {sd:.2f} |")

    return "\n".join(out)


def tabela_multi(dados: dict, tags: list[str]) -> str:
    faltando = [t for t in tags if t not in dados]
    if faltando:
        sys.exit(f"Tags ausentes: {faltando}. Disponiveis: {sorted(dados)}")

    out = ["### Comparativo entre execucoes", "",
           "| Metrica | " + " | ".join(tags) + " |",
           "|---------|" + "|".join(["---"] * len(tags)) + "|"]
    for rotulo, chave, fmt, _ in LINHAS:
        vals = [fmt.format(dados[t]["resumo"].get(chave, 0)) for t in tags]
        out.append(f"| {rotulo} | " + " | ".join(vals) + " |")
    out += ["", "| Config | " + " | ".join(tags) + " |",
            "|--------|" + "|".join(["---"] * len(tags)) + "|",
            "| Alvo | " + " | ".join(dados[t]["alvo"] for t in tags) + " |",
            "| Modelo | " + " | ".join(dados[t]["modelo"] for t in tags) + " |",
            "| Prompt | " + " | ".join(dados[t]["prompt"] for t in tags) + " |"]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", default="sprint2")
    ap.add_argument("--depois", default="sprint3")
    ap.add_argument("--tags", nargs="+", default=None,
                    help="Comparar N execucoes lado a lado em vez de antes/depois")
    ap.add_argument("--salvar", default=None, help="Grava a tabela num .md")
    args = ap.parse_args()

    dados = carregar()
    texto = (tabela_multi(dados, args.tags) if args.tags
             else tabela_antes_depois(dados, args.antes, args.depois))

    print("\n" + texto + "\n")
    if args.salvar:
        destino = config.RAIZ / args.salvar
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto + "\n", encoding="utf-8")
        print(f"Gravado em {destino}")


if __name__ == "__main__":
    main()
