"""
ChargeGrid AI — CLI interativo (Sprint 03).

Como rodar (PyCharm ou terminal, a partir da RAIZ do projeto):
    python src/backend/main.py

Diferenca para a Sprint 2: o CLI nao monta mais mensagem nenhuma. Ele so lê a
entrada, chama a chain LCEL e imprime. Toda a logica de prompt, memoria,
guardrail e schema mora em src/chain/ e src/guardrails/.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src import config
from src.chain.builder import construir_chain

# Console do Windows costuma vir em cp1252 e engasgar com UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BANNER = r"""
  ____  _                   _  ____      _     _      _    ___
 / ___|| |__   __ _ _ __ __| |/ ___|_ __(_) __| |    / \  |_ _|
| |    | '_ \ / _` | '__/ _` | |  _| '__| |/ _` |   / _ \  | |
| |___ | | | | (_| | | | (_| | |_| | |  | | (_| |  / ___ \ | |
 \____||_| |_|\__,_|_|  \__,_|\____|_|  |_|\__,_| /_/   \_\___|

  GoodWe EV Challenge 2026 | FIAP | Sprint 3 — nucleo em LangChain LCEL
  Assistente operacional de eletropostos comerciais
"""

SEP = "-" * 68

AJUDA = """
Comandos:
  /reset        Limpa o historico da sessao atual
  /status       Modelo, prompt e ocupacao da memoria
  /json <texto> Responde com saida estruturada validada (ConsultaRecarga)
  /prompt <v>   Troca a versao do system prompt (v1, v2, v3)
  /sessao <id>  Troca de sessao (cada id tem memoria propria)
  /ajuda        Esta mensagem
  /sair         Encerra
"""


def imprimir_status(chain, sessao: str) -> None:
    mem = chain.status_memoria(sessao)
    print(f"\n  Modelo   : {chain.modelo}")
    print(f"  Prompt   : {chain.versao_prompt}")
    print(f"  Sessao   : {sessao}")
    print(f"  Memoria  : {mem['mensagens']} msgs | {mem['tokens']}/{mem['teto']} tokens "
          f"({mem['ocupacao_pct']}%) | {mem['turnos_descartados']} turnos descartados")
    print(f"  Guardrail: {'ativo' if chain.guardrails_ativos else 'DESATIVADO'}\n")


def imprimir_estruturado(obj) -> None:
    print("\n  --- ConsultaRecarga (validado pelo Pydantic) ---")
    for campo, valor in obj.model_dump().items():
        if campo == "resposta_operador":
            continue
        print(f"  {campo:24} {valor}")
    print()


def run() -> None:
    ok, msg = config.checar_credenciais()
    print(BANNER)
    print(SEP)
    if not ok:
        print(msg)
        sys.exit(1)

    chain = construir_chain()
    sessao = "cli"
    imprimir_status(chain, sessao)
    print("  Digite sua mensagem ou /ajuda para ver os comandos.")
    print(SEP)

    while True:
        try:
            entrada = input("\nOperador > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEncerrando ChargeGrid AI.")
            return

        if not entrada:
            continue

        cmd = entrada.lower()

        if cmd == "/sair":
            print("\nEncerrando ChargeGrid AI.")
            return

        if cmd == "/ajuda":
            print(AJUDA)
            continue

        if cmd == "/reset":
            chain.resetar(sessao)
            print("\n  [Historico da sessao limpo.]")
            continue

        if cmd == "/status":
            imprimir_status(chain, sessao)
            continue

        if cmd.startswith("/sessao"):
            partes = entrada.split(maxsplit=1)
            if len(partes) == 2:
                sessao = partes[1].strip()
                print(f"\n  [Sessao ativa: {sessao}]")
                imprimir_status(chain, sessao)
            else:
                print("\n  Uso: /sessao <id>")
            continue

        if cmd.startswith("/prompt"):
            partes = entrada.split(maxsplit=1)
            if len(partes) == 2:
                try:
                    chain = construir_chain(versao_prompt=partes[1].strip())
                    print(f"\n  [Prompt {chain.versao_prompt} carregado.]")
                except FileNotFoundError as e:
                    print(f"\n  [ERRO] {e}")
            else:
                print("\n  Uso: /prompt v3")
            continue

        if cmd.startswith("/json"):
            partes = entrada.split(maxsplit=1)
            if len(partes) < 2:
                print("\n  Uso: /json <sua pergunta>")
                continue
            print("\nChargeGrid AI > ", end="", flush=True)
            r = chain.extrair(partes[1])
            print(r.texto)
            if r.estruturado:
                imprimir_estruturado(r.estruturado)
            print(f"  [{r.latencia_s:.2f}s | {r.tokens_total} tokens]")
            continue

        # Turno normal de conversa
        print("\nChargeGrid AI > ", end="", flush=True)
        r = chain.responder(entrada, session_id=sessao)
        print(r.texto)
        for aviso in r.avisos:
            print(f"\n  [AVISO] {aviso}")
        if r.bloqueado and r.motivo_bloqueio:
            print(f"\n  [guardrail: {r.motivo_bloqueio}]")
        print(f"\n  [{r.latencia_s:.2f}s | {r.tokens_total} tokens | origem: {r.origem}]")


if __name__ == "__main__":
    run()