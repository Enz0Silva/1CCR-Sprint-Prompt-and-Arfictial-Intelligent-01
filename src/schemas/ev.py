"""
Schemas Pydantic v2 do dominio EV — ChargeGrid AI (Aula 03).

ConsultaRecarga e o contrato de saida do chatbot quando a resposta precisa ser
consumida por codigo (dashboard, abertura de chamado, billing) e nao apenas lida
por um humano. O que o LLM devolve so vira objeto se passar pela validacao.

Uso na chain:
    parser = PydanticOutputParser(pydantic_object=ConsultaRecarga)
    prompt = ChatPromptTemplate...partial(format_instructions=parser.get_format_instructions())
    chain  = prompt | ChatOllama(..., format="json") | parser
"""
from __future__ import annotations

import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ── Vocabularios do dominio ────────────────────────────────────────────────
Intencao = Literal[
    "status_carregador",
    "diagnostico_falha",
    "faturamento",
    "load_balancing",
    "duvida_tecnica",
    "abertura_chamado",
    "fora_de_escopo",
]

EstadoCarregador = Literal[
    "disponivel",
    "ocupado",
    "em_falha",
    "indisponivel",
    "desconhecido",
]

Protocolo = Literal["OCPP 1.6J", "OCPP 2.0.1", "ISO 15118", "nao_aplicavel"]

# Codigos de erro que existem na base de conhecimento do prompt.
# Serve para barrar codigo inventado pelo modelo (regra critica 1 do system prompt).
PREFIXOS_ERRO_VALIDOS = ("EVC-OVERVOLT-", "EVC-UNDVOLT-", "EVC-COMM-", "EVC-TEMP-")

_RE_CARREGADOR = re.compile(r"^EVC-\d{2}$")


class SessaoRecarga(BaseModel):
    """Objeto aninhado — uma sessao de carga citada na resposta.

    Existe para que o modelo nao devolva numero solto em prosa: se ele cita
    energia ou valor, tem que dizer de qual sessao e de qual carregador.
    """

    carregador_id: str = Field(description="ID do carregador no padrao EVC-01 a EVC-99")
    energia_kwh: float = Field(ge=0, le=1000, description="Energia entregue na sessao, em kWh")
    duracao_min: int = Field(ge=0, le=1440, description="Duracao da sessao em minutos")
    valor_brl: Optional[float] = Field(
        None, ge=0, description="Valor faturado em reais; None se nao houver dado"
    )

    @field_validator("carregador_id")
    @classmethod
    def normalizar_id(cls, v: str) -> str:
        """Aceita '#3', 'evc-3', 'carregador 03' e normaliza para 'EVC-03'."""
        numero = re.search(r"(\d{1,2})", v or "")
        if not numero:
            raise ValueError("carregador_id sem numero identificavel (esperado EVC-01..EVC-99)")
        return f"EVC-{int(numero.group(1)):02d}"


class ConsultaRecarga(BaseModel):
    """Saida estruturada de uma consulta operacional ao ChargeGrid AI.

    ORDEM DOS CAMPOS IMPORTA. Quando o schema e passado ao `format=` do Ollama,
    a geracao e restrita por gramatica e segue a ordem declarada aqui. Se a
    geracao encurtar, os ultimos campos sao os que se perdem.

    Descoberto no eval: com 'resposta_operador' e 'proximo_passo' declarados no
    fim da classe, os casos P2 e P5 devolviam JSON com a classificacao completa e
    a resposta vazia ou ausente — ou seja, exatamente a parte que o operador le.
    Por isso os tres campos essenciais vem primeiro.
    """

    # --- Resposta ao operador (PRIMEIRO: nunca pode faltar) ---
    resposta_operador: str = Field(
        min_length=10,
        max_length=1500,
        description="Resposta em texto para o operador, em ASCII, objetiva e acionavel",
    )
    proximo_passo: str = Field(
        min_length=5,
        max_length=300,
        description="Proximo passo concreto sugerido ao operador",
    )
    confianca: float = Field(
        ge=0, le=1, description="Confianca do modelo na resposta, de 0 a 1"
    )

    # --- Classificacao ---
    intencao: Intencao = Field(description="Intencao principal detectada na pergunta do operador")
    dentro_do_escopo: bool = Field(
        description="True se a pergunta trata de operacao de eletropostos GoodWe"
    )

    # --- Dados operacionais ---
    carregador_id: Optional[str] = Field(
        None, description="ID do carregador citado, padrao EVC-01; None se nao houver"
    )
    estado_carregador: EstadoCarregador = Field(
        "desconhecido",
        description="Estado do carregador. Use 'desconhecido' se nao houver dado — nunca chute",
    )
    potencia_kw: Optional[float] = Field(
        None, ge=0, le=500, description="Potencia envolvida em kW (limite fisico da linha EV-C)"
    )
    codigo_erro: Optional[str] = Field(
        None, description="Codigo de erro GoodWe, ex.: EVC-OVERVOLT-03; None se nao houver"
    )
    protocolo: Protocolo = Field(
        "nao_aplicavel", description="Protocolo citado na resposta"
    )
    sessoes: List[SessaoRecarga] = Field(
        default_factory=list,
        description="Sessoes de recarga citadas. Lista vazia se nao houver dado — nao invente",
    )

    # --- Governanca ---
    dados_ausentes: List[str] = Field(
        default_factory=list,
        description="Campos que o operador pediu e nao ha dado disponivel",
    )
    requer_escalada_humana: bool = Field(
        False, description="True nos casos da secao <escalada_humana> do system prompt"
    )

    # ── Validators (Aula 03) ───────────────────────────────────────────────
    @field_validator("carregador_id")
    @classmethod
    def validar_formato_id(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza o ID do carregador ou rejeita o valor."""
        if v is None or str(v).strip() == "":
            return None
        v = str(v).strip().upper()
        if _RE_CARREGADOR.match(v):
            return v
        numero = re.search(r"(\d{1,2})", v)
        if not numero:
            raise ValueError(f"carregador_id invalido: '{v}' (esperado EVC-01..EVC-99)")
        return f"EVC-{int(numero.group(1)):02d}"

    @field_validator("codigo_erro")
    @classmethod
    def validar_codigo_erro(cls, v: Optional[str]) -> Optional[str]:
        """Barra codigo de erro fora da base de conhecimento.

        E aqui que o schema protege a regra critica 1 do system prompt: o modelo
        nao pode inventar um 'EVC-XYZ-99' que nao existe na documentacao GoodWe.
        """
        if v is None or str(v).strip() == "":
            return None
        v = str(v).strip().upper()
        if not v.startswith(PREFIXOS_ERRO_VALIDOS):
            raise ValueError(
                f"codigo_erro '{v}' nao pertence a base GoodWe. "
                f"Prefixos validos: {', '.join(PREFIXOS_ERRO_VALIDOS)}"
            )
        if not re.match(r"^EVC-[A-Z]+-\d{2}$", v):
            raise ValueError(f"codigo_erro '{v}' fora do padrao EVC-<TIPO>-<NN>")
        return v

    @field_validator("resposta_operador", "proximo_passo")
    @classmethod
    def exigir_ascii(cls, v: str) -> str:
        """O <formato> do system prompt exige ASCII; o schema faz valer.

        Em vez de rejeitar, transliteramos: rejeitar por causa de um acento
        desperdicaria uma resposta boa e uma chamada de modelo.
        """
        tabela = str.maketrans(
            "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
            "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
        )
        return v.translate(tabela).encode("ascii", "ignore").decode("ascii")

    @field_validator("confianca")
    @classmethod
    def arredondar_confianca(cls, v: float) -> float:
        return round(float(v), 2)

    @field_validator("sessoes")
    @classmethod
    def limitar_sessoes(cls, v: List[SessaoRecarga]) -> List[SessaoRecarga]:
        """Teto de 20 sessoes por resposta — acima disso e relatorio, nao consulta."""
        if len(v) > 20:
            raise ValueError("mais de 20 sessoes: use o relatorio de faturamento, nao a consulta")
        return v


# ── Schema secundario: relatorio agregado ──────────────────────────────────
class RelatorioFaturamento(BaseModel):
    """Saida estruturada do relatorio de faturamento por periodo."""

    periodo: str = Field(description="Periodo do relatorio, formato AAAA-MM")
    total_sessoes: int = Field(ge=0, description="Numero de sessoes no periodo")
    energia_total_kwh: float = Field(ge=0, description="Energia total entregue em kWh")
    receita_bruta_brl: float = Field(ge=0, description="Receita bruta em reais")
    dados_disponiveis: bool = Field(
        description="False quando nao ha integracao com o backend de billing"
    )
    observacao: str = Field(max_length=500, description="Observacao ou ressalva do relatorio")

    @field_validator("periodo")
    @classmethod
    def validar_periodo(cls, v: str) -> str:
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", str(v).strip()):
            raise ValueError(f"periodo '{v}' fora do formato AAAA-MM")
        return str(v).strip()
