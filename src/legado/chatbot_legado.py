"""
Versao LEGADO (Sprints 1/2) — preservada apenas para o comparativo antes/depois.

Este arquivo e uma copia funcional do antigo src/backend/chatbot.py, com duas
adicoes: instrumentacao de latencia/tokens e a mesma interface `Resposta` da
chain nova. Sem isso, a tabela obrigatoria do §8 seria chute — com isso, os
dois lados sao medidos com o mesmo criterio, na mesma maquina, no mesmo dia.

NAO evoluir este arquivo. Ele e o baseline congelado.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ollama import Client

from src import config
from src.chain.builder import Resposta
from src.chain.memoria import contar_tokens


class ChatbotLegado:
    """Chatbot manual da Sprint 2: lista de dicts que so cresce."""

    def __init__(self, modelo: str = config.MODELO_PADRAO,
                 versao_prompt: str = "v1") -> None:
        self.modelo = modelo
        self.versao_prompt = versao_prompt
        self.system_prompt = config.carregar_system_prompt(versao_prompt)
        self.client = Client(
            host=config.OLLAMA_HOST,
            headers={"Authorization": "Bearer " + config.OLLAMA_API_KEY},
        )
        self.historico = [{"role": "system", "content": self.system_prompt}]

    def responder(self, pergunta: str, session_id: str = "legado") -> Resposta:
        """Mesma assinatura da chain nova — o eval roda os dois sem if.

        session_id e ignorado de proposito: a versao legado nao tinha sessao,
        o historico era global ao processo. Essa limitacao e um dos itens do
        comparativo.
        """
        self.historico.append({"role": "user", "content": pergunta})
        tokens_entrada = sum(contar_tokens(m["content"]) for m in self.historico)

        inicio = time.perf_counter()
        try:
            bruto = self.client.chat(
                model=self.modelo,
                messages=self.historico,
                options={"num_predict": 1024, "temperature": 0.3},
                stream=False,
            )
            texto = bruto["message"]["content"].strip()
        except Exception as e:
            return Resposta(
                texto=f"[ERRO] {e}",
                origem="erro",
                latencia_s=time.perf_counter() - inicio,
                tokens_entrada=tokens_entrada,
                bloqueado=True,
                motivo_bloqueio="excecao",
            )
        latencia = time.perf_counter() - inicio

        self.historico.append({"role": "assistant", "content": texto})

        return Resposta(
            texto=texto,
            origem="llm",
            latencia_s=latencia,
            tokens_entrada=tokens_entrada,
            tokens_saida=contar_tokens(texto),
        )

    def extrair(self, pergunta: str) -> Resposta:
        """A Sprint 2 nao tinha saida estruturada.

        Retorna sempre falha de schema — e exatamente esse zero que aparece na
        linha "acuracia do structured output" da tabela antes/depois.
        """
        r = self.responder(pergunta)
        r.estruturado = None
        r.motivo_bloqueio = "sem_structured_output_na_sprint2"
        return r

    def status_memoria(self, session_id: str = "legado") -> dict:
        tokens = sum(contar_tokens(m["content"]) for m in self.historico)
        return {
            "mensagens": len(self.historico),
            "tokens": tokens,
            "teto": None,               # nao existia teto
            "ocupacao_pct": None,
            "turnos_descartados": 0,    # nada era descartado: o custo so subia
        }

    def resetar(self, session_id: str = "legado") -> None:
        self.historico = [{"role": "system", "content": self.system_prompt}]


if __name__ == "__main__":
    bot = ChatbotLegado()
    for t in ["O carregador 3 parou. O que houve?",
              "E quanto tempo leva?",
              "De qual carregador eu falei?"]:
        r = bot.responder(t)
        print(f"[{r.latencia_s:.2f}s | {r.tokens_total} tokens] {t}")
        print(r.texto[:300], "\n")
        print("memoria:", bot.status_memoria(), "\n")
