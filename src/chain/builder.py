"""
Chain LCEL do ChargeGrid AI — o nucleo conversacional refatorado (Sprint 03).

Antes (Sprints 1/2), em src/backend/chatbot.py:

    history.append({"role": "user", "content": msg})
    resposta = client.chat(model=..., messages=history, options={...})
    reply = resposta["message"]["content"].strip()
    history.append({"role": "assistant", "content": reply})

Agora:

    prompt | llm | parser            (Aula 01)
    + RunnableWithMessageHistory     (Aula 02)
    + PydanticOutputParser           (Aula 03)
    + system prompt versionado       (Aula 04)
    + guardrails de entrada e saida  (§6 do enunciado)

Duas chains, como na Aula 03:
  - conversa  : memoria por sessao, saida em texto  -> responder(...)
  - extracao  : sem memoria, saida ConsultaRecarga  -> extrair(...)
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from src import config
from src.chain.memoria import contar_tokens, get_session_history
from src.guardrails import moderation, scope_validator
from src.schemas.ev import ConsultaRecarga


@dataclass
class Resposta:
    """Resposta do chatbot + instrumentacao que alimenta o eval e o /status."""

    texto: str
    origem: str                     # "llm" | "guardrail_escopo" | "guardrail_moderacao"
    latencia_s: float = 0.0
    tokens_entrada: int = 0
    tokens_saida: int = 0
    bloqueado: bool = False
    motivo_bloqueio: Optional[str] = None
    avisos: list[str] = field(default_factory=list)
    estruturado: Optional[ConsultaRecarga] = None

    @property
    def tokens_total(self) -> int:
        return self.tokens_entrada + self.tokens_saida

    def para_dict(self) -> dict[str, Any]:
        d = {
            "texto": self.texto,
            "origem": self.origem,
            "latencia_s": round(self.latencia_s, 3),
            "tokens_entrada": self.tokens_entrada,
            "tokens_saida": self.tokens_saida,
            "tokens_total": self.tokens_total,
            "bloqueado": self.bloqueado,
            "motivo_bloqueio": self.motivo_bloqueio,
            "avisos": self.avisos,
        }
        if self.estruturado is not None:
            d["estruturado"] = self.estruturado.model_dump()
        return d


class ChargeGridChain:
    """Encapsula as duas chains e as camadas de guardrail."""

    def __init__(
        self,
        modelo: str = config.MODELO_PADRAO,
        versao_prompt: str = config.PROMPT_VERSAO_PADRAO,
        max_tokens_historico: int = config.MAX_TOKENS_HISTORICO,
        params_chat: dict | None = None,
        guardrails_ativos: bool = True,
    ) -> None:
        self.modelo = modelo
        self.versao_prompt = versao_prompt
        self.max_tokens_historico = max_tokens_historico
        self.params_chat = params_chat or config.PARAMS_CHAT
        self.guardrails_ativos = guardrails_ativos
        self.system_prompt = config.carregar_system_prompt(versao_prompt)

        self._montar_chain_conversa()
        self._montar_chain_extracao()

    def _host_e_modelo(self) -> tuple[str, str]:
        """Resolve o prefixo 'local:' para o host correto.

        'local:gemma3:4b' -> (http://localhost:11434, 'gemma3:4b')
        'gpt-oss:120b'    -> (https://ollama.com,     'gpt-oss:120b')

        Permite rodar a chain e o eval contra um modelo na maquina do grupo,
        sem que nenhum dado saia da rede interna.
        """
        if self.modelo.startswith("local:"):
            return config.OLLAMA_HOST_LOCAL, self.modelo.split(":", 1)[1]
        return config.OLLAMA_HOST, self.modelo

    # ── Chain 1: conversa com memoria ──────────────────────────────────────
    def _montar_chain_conversa(self) -> None:
        # MessagesPlaceholder e o ponto onde RunnableWithMessageHistory injeta
        # o historico da sessao. Sem ele, a chain volta a ser stateless.
        self.prompt_conversa = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{pergunta}"),
        ]).partial(system_prompt=self.system_prompt)

        host, modelo = self._host_e_modelo()
        self.llm_conversa = ChatOllama(
            model=modelo,
            base_url=host,
            **self.params_chat,
        )

        chain_base = self.prompt_conversa | self.llm_conversa | StrOutputParser()

        self.chain_conversa = RunnableWithMessageHistory(
            chain_base,
            lambda sid: get_session_history(sid, self.max_tokens_historico),
            input_messages_key="pergunta",
            history_messages_key="history",
        )

    # ── Chain 2: extracao estruturada (sem memoria) ────────────────────────
    def _montar_chain_extracao(self) -> None:
        self.parser_pydantic = PydanticOutputParser(pydantic_object=ConsultaRecarga)

        self.prompt_extracao = ChatPromptTemplate.from_messages([
            ("system",
             "{system_prompt}\n\n"
             "<saida_estruturada>\n"
             "Responda SOMENTE com o JSON do schema abaixo. Sem texto fora do JSON.\n"
             "TODOS os campos obrigatorios devem estar presentes — em especial\n"
             "'resposta_operador', 'proximo_passo' e 'confianca', que sao o que o\n"
             "operador efetivamente le. JSON sem eles e descartado pela validacao.\n"
             "Campo sem dado disponivel: use null, lista vazia ou 'desconhecido' — "
             "nunca preencha por suposicao.\n"
             "{format_instructions}\n"
             "</saida_estruturada>"),
            ("human", "{pergunta}"),
        ]).partial(
            system_prompt=self.system_prompt,
            format_instructions=self.parser_pydantic.get_format_instructions(),
        )

        # format= aceita o JSON Schema do Pydantic nas versoes recentes do
        # langchain-ollama. Com o schema, o Ollama restringe a GERACAO aos campos
        # certos; com format="json" ele so garante que a saida seja JSON valido.
        #
        # Por que importa: no eval, o caso P5 devolvia JSON sintaticamente valido
        # mas sem 'resposta_operador' nem 'proximo_passo'. O modelo nao tinha como
        # saber que eram obrigatorios — a string "json" nao carrega o schema.
        host, modelo = self._host_e_modelo()
        try:
            self.llm_json = ChatOllama(
                model=modelo,
                base_url=host,
                format=ConsultaRecarga.model_json_schema(),
                **config.PARAMS_STRUCT,
            )
            self.formato_structured = "json_schema"
        except Exception:
            # Fallback para versoes que so aceitam a string "json".
            self.llm_json = ChatOllama(
                model=modelo,
                base_url=host,
                format="json",
                **config.PARAMS_STRUCT,
            )
            self.formato_structured = "json"

        self.chain_extracao = self.prompt_extracao | self.llm_json | self.parser_pydantic

    # ── API publica ────────────────────────────────────────────────────────
    def responder(self, pergunta: str, session_id: str = "cli") -> Resposta:
        """Turno de conversa com memoria e guardrails."""
        if self.guardrails_ativos:
            mod = moderation.moderar_entrada(pergunta)
            if mod.bloqueado:
                return Resposta(
                    texto=mod.resposta_pronta,
                    origem="guardrail_moderacao",
                    bloqueado=True,
                    motivo_bloqueio=",".join(mod.categorias),
                    tokens_saida=contar_tokens(mod.resposta_pronta),
                )

            escopo = scope_validator.validar_escopo(pergunta)
            if escopo.bloqueado:
                return Resposta(
                    texto=escopo.resposta_pronta,
                    origem="guardrail_escopo",
                    bloqueado=True,
                    motivo_bloqueio=escopo.motivo,
                    tokens_saida=contar_tokens(escopo.resposta_pronta),
                )

        historico = get_session_history(session_id, self.max_tokens_historico)
        tokens_entrada = (
            contar_tokens(self.system_prompt)
            + historico.tokens_no_buffer()
            + contar_tokens(pergunta)
        )

        inicio = time.perf_counter()
        try:
            texto = self.chain_conversa.invoke(
                {"pergunta": pergunta},
                config={"configurable": {"session_id": session_id}},
            )
        except Exception as e:
            return Resposta(
                texto=f"[ERRO] Falha ao consultar o modelo {self.modelo}: {e}",
                origem="erro",
                latencia_s=time.perf_counter() - inicio,
                tokens_entrada=tokens_entrada,
                bloqueado=True,
                motivo_bloqueio="excecao",
            )
        latencia = time.perf_counter() - inicio

        avisos: list[str] = []
        if self.guardrails_ativos:
            saida = moderation.moderar_saida(texto)
            if saida.bloqueado:
                return Resposta(
                    texto=saida.resposta_pronta,
                    origem="guardrail_moderacao",
                    latencia_s=latencia,
                    tokens_entrada=tokens_entrada,
                    tokens_saida=contar_tokens(saida.resposta_pronta),
                    bloqueado=True,
                    motivo_bloqueio="saida:" + ",".join(saida.categorias),
                )
            suspeitas = scope_validator.checar_specs_inventadas(texto)
            if suspeitas:
                aviso = ("Possivel especificacao fora da base de conhecimento: "
                         + ", ".join(suspeitas))
                avisos.append(aviso)
                # O aviso precisa chegar ao operador, nao so ao log.
                #
                # Descoberto no eval: no caso E1 o modelo inventou a especificacao
                # "GoodWe EV-C 450 Pro - 450 kW" para um produto inexistente. O
                # detector marcou corretamente, mas o aviso ficava guardado no campo
                # `avisos`, que nem o CLI imprimia em destaque nem o eval pontuava.
                # Guardrail que ninguem le nao e guardrail.
                texto = (
                    "[NAO CONFIRMADO] Os dados de produto abaixo nao constam na base "
                    "de conhecimento GoodWe carregada. Nao use como especificacao "
                    "oficial sem confirmar no manual tecnico ou com o suporte.\n\n"
                    + texto
                )

        return Resposta(
            texto=texto,
            origem="llm",
            latencia_s=latencia,
            tokens_entrada=tokens_entrada,
            tokens_saida=contar_tokens(texto),
            avisos=avisos,
        )

    def extrair(self, pergunta: str) -> Resposta:
        """Consulta com saida validada pelo schema ConsultaRecarga."""
        if self.guardrails_ativos:
            mod = moderation.moderar_entrada(pergunta)
            if mod.bloqueado:
                return Resposta(
                    texto=mod.resposta_pronta,
                    origem="guardrail_moderacao",
                    bloqueado=True,
                    motivo_bloqueio=",".join(mod.categorias),
                )

        tokens_entrada = contar_tokens(self.system_prompt) + contar_tokens(pergunta)
        inicio = time.perf_counter()
        try:
            objeto: ConsultaRecarga = self.chain_extracao.invoke({"pergunta": pergunta})
        except ValidationError as e:
            # O schema barrou a saida. E sucesso do guardrail, nao bug:
            # o dado invalido nao chega ao operador nem ao sistema de billing.
            detalhe = "; ".join(f"{err['loc']}: {err['msg']}" for err in e.errors()[:4])
            return Resposta(
                texto=f"[SCHEMA INVALIDO] {detalhe}",
                origem="erro",
                latencia_s=time.perf_counter() - inicio,
                tokens_entrada=tokens_entrada,
                bloqueado=True,
                motivo_bloqueio="validation_error",
            )
        except Exception as e:
            return Resposta(
                texto=f"[ERRO] {e}",
                origem="erro",
                latencia_s=time.perf_counter() - inicio,
                bloqueado=True,
                motivo_bloqueio="excecao",
            )
        latencia = time.perf_counter() - inicio

        return Resposta(
            texto=objeto.resposta_operador,
            origem="llm",
            latencia_s=latencia,
            tokens_entrada=tokens_entrada,
            tokens_saida=contar_tokens(objeto.model_dump_json()),
            estruturado=objeto,
        )

    # ── utilitarios ────────────────────────────────────────────────────────
    def status_memoria(self, session_id: str = "cli") -> dict:
        return get_session_history(session_id, self.max_tokens_historico).resumo()

    def resetar(self, session_id: str = "cli") -> None:
        get_session_history(session_id, self.max_tokens_historico).clear()


def construir_chain(**kwargs) -> ChargeGridChain:
    """Atalho usado pelo CLI, pelo eval e pelo multi_provider."""
    return ChargeGridChain(**kwargs)


if __name__ == "__main__":
    ok, msg = config.checar_credenciais()
    print(msg)
    if not ok:
        sys.exit(1)

    chain = construir_chain()
    print(f"Modelo: {chain.modelo} | Prompt: {chain.versao_prompt}\n")

    # Demonstracao de memoria em 3+ turnos (exigencia do bloco A da rubrica)
    turnos = [
        "O carregador 3 parou no meio da sessao. O que pode ter acontecido?",
        "E quanto tempo leva para resolver isso?",
        "Voce lembra de qual carregador eu estava falando?",
        "Abre um chamado para ele entao.",
    ]
    for i, t in enumerate(turnos, 1):
        r = chain.responder(t, session_id="demo")
        print(f"--- Turno {i} | {r.latencia_s:.2f}s | {r.tokens_total} tokens ---")
        print(f"Operador > {t}")
        print(f"ChargeGrid > {r.texto[:400]}\n")
        print(f"memoria: {chain.status_memoria('demo')}\n")
