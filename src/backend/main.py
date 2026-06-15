"""
ChargeGrid AI — CLI Interativo
GoodWe EV Challenge 2026 | FIAP 1CCR Sprint 2
"""
import sys
from chatbot import build_history, chat, reset_history, OLLAMA_MODEL, OLLAMA_URL

BANNER = r"""
  ____  _                   _  ____      _     _      _    ___ 
 / ___|| |__   __ _ _ __ __| |/ ___|_ __(_) __| |    / \  |_ _|
| |    | '_ \ / _` | '__/ _` | |  _| '__| |/ _` |   / _ \  | | 
| |___ | | | | (_| | | | (_| | |_| | |  | | (_| |  / ___ \ | | 
 \____||_| |_|\__,_|_|  \__,_|\____|_|  |_|\__,_| /_/   \_\___|

  GoodWe EV Challenge 2026 | FIAP 1CCR | Sprint 2
  Assistente operacional de eletropostos comerciais
"""

SEPARATOR = "─" * 60

HELP_TEXT = """
Comandos especiais:
  /reset    — Limpa o historico de conversa
  /status   — Mostra modelo e URL do Ollama
  /ajuda    — Exibe esta mensagem
  /sair     — Encerra o chatbot
"""


def print_status():
    print(f"\n  Modelo : {OLLAMA_MODEL}")
    print(f"  Ollama : {OLLAMA_URL}")
    print(f"  Memoria: historico ativo\n")


def run():
    print(BANNER)
    print(SEPARATOR)
    print_status()
    print("  Digite sua mensagem ou /ajuda para ver os comandos.")
    print(SEPARATOR)

    history = build_history()

    while True:
        try:
            user_input = input("\nOperador > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nEncerrando ChargeGrid AI. Ate logo.")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() == "/sair":
            print("\nEncerrando ChargeGrid AI. Ate logo.")
            sys.exit(0)

        elif user_input.lower() == "/reset":
            history = reset_history()
            print("\n  [Historico resetado. Nova conversa iniciada.]\n")
            continue

        elif user_input.lower() == "/status":
            print_status()
            continue

        elif user_input.lower() == "/ajuda":
            print(HELP_TEXT)
            continue

        print("\nChargeGrid AI > ", end="", flush=True)
        try:
            response = chat(history, user_input)
            print(response)
            print()
        except Exception as e:
            print(f"\n  [ERRO] {e}\n")


if __name__ == "__main__":
    run()