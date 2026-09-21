"""
Memoria conversacional por sessao — ChargeGrid AI (Aula 02).

O problema herdado da Sprint 2: `history` era uma lista Python que so crescia.
A cada turno o historico inteiro voltava para o modelo, o custo por turno subia
de forma linear e, numa sessao longa de operador, estourava a janela de contexto.

A solucao aqui e a mesma ideia da ConversationTokenBufferMemory da Aula 02 —
janela deslizante com teto explicito de tokens — mas implementada como um
BaseChatMessageHistory, porque e isso que o RunnableWithMessageHistory consome
na chain LCEL. A ConversationTokenBufferMemory original so encaixa na
ConversationChain legada, que nao usamos mais.

A funcao `criar_memoria_classic()` no fim do arquivo instancia a classe original
da aula — usada em evals/ para provar que a politica de descarte e equivalente.
"""
from __future__ import annotations

from typing import Dict, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, SystemMessage
from pydantic import Field

try:
    import tiktoken

    _ENC = tiktoken.get_encoding("cl100k_base")

    def contar_tokens(texto: str) -> int:
        """Contagem real via BPE (Aula 04)."""
        return len(_ENC.encode(texto or ""))

except Exception:  # pragma: no cover - fallback sem tiktoken instalado
    def contar_tokens(texto: str) -> int:
        """Aproximacao por caracteres quando tiktoken nao esta disponivel."""
        return max(1, len(texto or "") // 4)


class MemoriaTokenBuffer(BaseChatMessageHistory):
    """Historico de uma sessao com teto de tokens e descarte das mais antigas.

    Politica de descarte:
      - mensagens sao removidas do INICIO (as mais antigas) ate caber no teto;
      - o descarte e feito em PARES (pergunta + resposta), porque cortar so a
        resposta deixa a pergunta orfa e confunde o modelo no turno seguinte;
      - a ultima mensagem nunca e descartada, mesmo se sozinha ja estourar
        o limite — sem ela nao ha turno.
    """

    messages: List[BaseMessage] = Field(default_factory=list)

    def __init__(self, max_token_limit: int = 800) -> None:
        super().__init__()
        self.max_token_limit = max_token_limit
        self.messages = []
        self.turnos_descartados = 0

    # --- interface exigida pelo LangChain ---
    def add_message(self, message: BaseMessage) -> None:
        self.messages.append(message)
        self._aparar()

    def add_messages(self, messages: List[BaseMessage]) -> None:
        self.messages.extend(messages)
        self._aparar()

    def clear(self) -> None:
        self.messages = []
        self.turnos_descartados = 0

    # --- politica de janela deslizante ---
    def _aparar(self) -> None:
        while len(self.messages) > 1 and self.tokens_no_buffer() > self.max_token_limit:
            # nunca descarta um SystemMessage que porventura tenha entrado no historico
            if isinstance(self.messages[0], SystemMessage):
                if len(self.messages) < 3:
                    break
                del self.messages[1:3]
            else:
                del self.messages[0:2]
            self.turnos_descartados += 1

    # --- instrumentacao (usada pelo /status do CLI e pelo eval) ---
    def tokens_no_buffer(self) -> int:
        return sum(contar_tokens(str(m.content)) for m in self.messages)

    def resumo(self) -> dict:
        return {
            "mensagens": len(self.messages),
            "tokens": self.tokens_no_buffer(),
            "teto": self.max_token_limit,
            "ocupacao_pct": round(
                100 * self.tokens_no_buffer() / max(1, self.max_token_limit), 1
            ),
            "turnos_descartados": self.turnos_descartados,
        }

    def __repr__(self) -> str:  # pragma: no cover
        r = self.resumo()
        return (f"<MemoriaTokenBuffer {r['mensagens']} msgs | "
                f"{r['tokens']}/{r['teto']} tokens | "
                f"{r['turnos_descartados']} turnos descartados>")


# ── Store multi-sessao ─────────────────────────────────────────────────────
_STORE: Dict[str, MemoriaTokenBuffer] = {}


def get_session_history(session_id: str,
                        max_token_limit: int = 800) -> MemoriaTokenBuffer:
    """Devolve o historico da sessao, criando na primeira vez.

    Cada operador (ou cada aba do CLI) tem seu session_id: dois operadores
    conversando ao mesmo tempo nao misturam contexto.
    """
    if session_id not in _STORE:
        _STORE[session_id] = MemoriaTokenBuffer(max_token_limit=max_token_limit)
    return _STORE[session_id]


def limpar_sessao(session_id: str) -> None:
    if session_id in _STORE:
        _STORE[session_id].clear()


def sessoes_ativas() -> list[str]:
    return sorted(_STORE.keys())


def estado_store() -> dict:
    return {sid: mem.resumo() for sid, mem in _STORE.items()}


# ── Paridade com a Aula 02 ────────────────────────────────────────────────
def criar_memoria_classic(llm, max_token_limit: int = 800):
    """Instancia a ConversationTokenBufferMemory original da Aula 02.

    Nao e usada na chain de producao (nao encaixa em RunnableWithMessageHistory),
    mas e chamada em evals/ para comparar a politica de descarte das duas
    implementacoes lado a lado.
    """
    from langchain_classic.memory import ConversationTokenBufferMemory

    return ConversationTokenBufferMemory(
        llm=llm,
        max_token_limit=max_token_limit,
        memory_key="history",
        return_messages=True,
    )


if __name__ == "__main__":
    from langchain_core.messages import AIMessage, HumanMessage

    mem = MemoriaTokenBuffer(max_token_limit=120)
    for i in range(1, 9):
        mem.add_message(HumanMessage(content=f"Turno {i}: status do carregador EVC-0{i}?"))
        mem.add_message(AIMessage(content=f"Carregador EVC-0{i} disponivel. Proximo passo: monitorar."))
        print(f"turno {i}: {mem.resumo()}")
    print("\nMensagens restantes:", [m.content[:38] for m in mem.messages])
