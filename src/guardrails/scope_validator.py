"""
Guardrail de escopo — ChargeGrid AI (Sprint 03, §6).

Tres decisoes, tomadas em codigo ANTES de gastar uma chamada de modelo:

1. DENTRO DO ESCOPO  -> segue para a chain.
2. DOMINIO RESTRITO  -> juridico, financeiro ou seguranca eletrica: recusa com
                        orientacao a profissional habilitado.
3. FORA DO ESCOPO    -> resposta canonica de redirecionamento.

Por que em codigo e nao so no prompt: prompt e defesa probabilistica, o modelo
pode escorregar em um turno. Regex e deterministico e custa zero token. As duas
camadas convivem — o prompt v3 tem as mesmas regras em <dominios_restritos>.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal, Optional

Decisao = Literal["permitido", "dominio_restrito", "fora_de_escopo"]


@dataclass
class ResultadoEscopo:
    decisao: Decisao
    motivo: str
    resposta_pronta: Optional[str] = None
    termos: Optional[list[str]] = None

    @property
    def bloqueado(self) -> bool:
        return self.decisao != "permitido"


# ── Vocabulario do dominio GoodWe / eletropostos ───────────────────────────
TERMOS_ESCOPO = [
    "carregador", "carregadores", "eletroposto", "eletropostos", "recarga",
    "carga", "sessao", "sessoes", "kwh", "kw", "potencia", "ocpp", "iso 15118",
    "plug & charge", "plug and charge", "goodwe", "ev-c", "evc", "ccs2",
    "chademo", "tipo 2", "load balancing", "balanceamento", "firmware", "ota",
    "rfid", "conector", "faturamento", "billing", "tarifa", "chamado",
    "manutencao", "diagnostico", "log", "erro", "falha", "overvolt", "undvolt",
    "sobretensao", "subtensao", "veiculo eletrico", "ve ", "posto", "backend",
    "status", "disponivel", "ocupado", "consumo", "energia", "quadro",
]

# ── Temas claramente fora do escopo ────────────────────────────────────────
# Necessario porque termos do dominio sao ambiguos: "restaurante perto do POSTO"
# contem "posto" e passaria no filtro de escopo. Esta lista tem precedencia.
TERMOS_FORA_ESCOPO = [
    "restaurante", "almocar", "jantar", "lanchonete", "padaria", "bar ",
    "cerveja", "pizza", "delivery", "ifood",
    "futebol", "jogo do", "campeonato", "escalacao", "time de futebol",
    "filme", "serie de tv", "netflix", "musica", "playlist", "novela",
    "piada", "poema", "conte uma historia", "escreva um conto",
    "horoscopo", "signo", "loteria", "mega sena",
    "namorad", "relacionamento amoroso", "presente de aniversario",
    "receita de bolo", "receita de comida", "como cozinhar",
    "previsao do tempo", "vai chover", "temperatura hoje",
    "quem ganhou a eleicao", "politica nacional", "presidente do brasil",
    "traduza para", "faca meu trabalho de", "resolva essa equacao",
    "melhor celular", "comprar carro", "viagem para",
]

# ── Dominios restritos: recusar conselho, orientar profissional ────────────
DOMINIOS_RESTRITOS: dict[str, dict] = {
    "juridico": {
        "termos": [
            "processo", "processar", "advogado", "juridico", "clausula",
            "contrato de locacao", "rescisao", "multa contratual", "lgpd",
            "acao judicial", "indenizacao", "responsabilidade civil", "intimacao",
            "notificacao extrajudicial", "codigo de defesa do consumidor",
        ],
        "profissional": "um advogado ou o juridico da sua empresa",
        "pode_fazer": "levantar o historico de sessoes e os logs do equipamento "
                      "que voces vao precisar como evidencia",
    },
    "financeiro": {
        "termos": [
            "investir", "investimento", "payback", "roi", "financiamento",
            "emprestimo", "credito", "imposto", "tributacao", "icms", "irpj",
            "declarar", "contabil", "fluxo de caixa", "valuation", "acoes",
            "aplicacao financeira", "rentabilidade do investimento",
        ],
        "profissional": "um contador ou a area financeira da sua empresa",
        "pode_fazer": "gerar o relatorio de consumo e faturamento por periodo "
                      "que alimenta essa analise",
    },
    "seguranca_eletrica": {
        "termos": [
            "dimensionar disjuntor", "trocar disjuntor", "aterramento",
            "mexer no quadro", "quadro energizado", "sem desligar a chave",
            "fazer a ligacao eu mesmo", "puxar um cabo", "gambiarra", "jumper",
            "bypass da protecao", "desativar a protecao", "burlar o disjuntor",
            "ligar direto na rede", "improvisar a fiacao", "emendar o cabo",
        ],
        "profissional": "um eletricista ou engenheiro eletricista com ART",
        "pode_fazer": "explicar o codigo de erro registrado e abrir o chamado "
                      "tecnico para a GoodWe",
    },
}

TEMPLATE_RESTRITO = (
    "Isso esta fora do que eu posso orientar: {assunto} exige avaliacao de "
    "{profissional}. Nao vou opinar aqui porque uma resposta errada tem custo "
    "real para voces.\n\n"
    "O que eu posso fazer agora: {pode_fazer}.\n\n"
    "Proximo passo: me diga se quer que eu prepare esse material."
)

RESPOSTA_FORA_DE_ESCOPO = (
    "Fora do escopo do ChargeGrid AI. Consulte o suporte GoodWe ou o responsavel "
    "tecnico da sua empresa para assuntos nao relacionados a operacao de eletropostos.\n\n"
    "Proximo passo: se precisar, posso consultar status de carregador, log de "
    "falha, faturamento ou plano de Load Balancing."
)

_NOMES_AMIGAVEIS = {
    "juridico": "assunto juridico",
    "financeiro": "decisao financeira",
    "seguranca_eletrica": "intervencao em instalacao eletrica",
}


def normalizar(texto: str) -> str:
    """Minusculas sem acento — para o regex nao depender de como o operador digitou."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def _encontrar(texto_norm: str, termos: list[str]) -> list[str]:
    achados = []
    for termo in termos:
        padrao = r"\b" + re.escape(termo).replace(r"\ ", r"\s+")
        if re.search(padrao, texto_norm):
            achados.append(termo)
    return achados


def validar_escopo(pergunta: str) -> ResultadoEscopo:
    """Classifica a pergunta do operador antes de chamar o modelo."""
    texto = normalizar(pergunta)

    if len(texto.strip()) < 3:
        return ResultadoEscopo("fora_de_escopo", "mensagem vazia ou curta demais",
                               RESPOSTA_FORA_DE_ESCOPO)

    # 1) Dominio restrito tem precedencia: "posso processar a GoodWe pelo carregador
    #    queimado?" tem termo do escopo, mas a pergunta e juridica.
    for dominio, cfg in DOMINIOS_RESTRITOS.items():
        achados = _encontrar(texto, cfg["termos"])
        if achados:
            resposta = TEMPLATE_RESTRITO.format(
                assunto=_NOMES_AMIGAVEIS[dominio],
                profissional=cfg["profissional"],
                pode_fazer=cfg["pode_fazer"],
            )
            return ResultadoEscopo("dominio_restrito",
                                   f"dominio restrito: {dominio}", resposta, achados)

    # 2) Tema explicitamente fora do escopo tem precedencia sobre o vocabulario
    #    do dominio: "restaurante perto do posto" contem "posto", mas nao e
    #    pergunta de operacao de eletroposto.
    achados = _encontrar(texto, TERMOS_FORA_ESCOPO)
    if achados:
        return ResultadoEscopo("fora_de_escopo", f"tema fora do escopo: {achados[0]}",
                               RESPOSTA_FORA_DE_ESCOPO, achados)

    # 3) Escopo operacional GoodWe
    achados = _encontrar(texto, TERMOS_ESCOPO)
    if achados:
        return ResultadoEscopo("permitido", "termo de dominio encontrado",
                               termos=achados)

    # 4) Continuidade de conversa (o turno anterior deu o contexto)
    if re.search(r"\b(e (o|a|isso|entao)|e quanto|por que|qual (deles|era)|"
                 r"me explica|detalha|continua|sim|ok|confirmo|pode)\b", texto):
        return ResultadoEscopo("permitido", "provavel continuacao de turno anterior")

    return ResultadoEscopo("fora_de_escopo", "nenhum termo do dominio encontrado",
                           RESPOSTA_FORA_DE_ESCOPO)


# ── Anti-alucinacao de especificacao de produto ────────────────────────────
MODELOS_CONHECIDOS = {"ev-c", "evc"}
_RE_MODELO_INVENTADO = re.compile(
    r"\b(?:goodwe\s+)?(?:ev[-\s]?[a-z]{1,3}\s?\d{2,4}|gw[-\s]?\d{2,4}[a-z]{0,3})\b"
)


def checar_specs_inventadas(resposta: str) -> list[str]:
    """Procura modelo/spec de produto que nao esta na base de conhecimento.

    Roda DEPOIS do modelo responder. Nao bloqueia — marca para o operador,
    porque falso positivo aqui e mais provavel que alucinacao real.
    """
    texto = normalizar(resposta)
    suspeitas = []
    for achado in set(_RE_MODELO_INVENTADO.findall(texto)):
        if achado.strip() not in MODELOS_CONHECIDOS:
            suspeitas.append(achado.strip())
    return sorted(suspeitas)


if __name__ == "__main__":
    testes = [
        "Quantos carregadores estao disponiveis no posto da Paulista?",
        "Posso processar a GoodWe pelo carregador que queimou?",
        "Vale a pena investir em mais 10 carregadores? Qual o payback?",
        "Como eu mexo no quadro energizado sem desligar a chave?",
        "Me recomenda um restaurante perto do posto?",
        "E quanto tempo leva?",
    ]
    for t in testes:
        r = validar_escopo(t)
        print(f"[{r.decisao:17}] {t}\n                    -> {r.motivo}")
