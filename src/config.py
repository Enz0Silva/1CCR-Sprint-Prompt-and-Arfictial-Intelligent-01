"""
ChargeGrid AI — configuracao central (Sprint 03).

Concentra caminhos, variaveis de ambiente e parametros de modelo num lugar so,
para que builder.py, run_eval.py e multi_provider.py leiam sempre a mesma fonte.

Credenciais: apenas via .env (gitignored). Nada de chave no codigo.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

# ── Caminhos ────────────────────────────────────────────────────────────────
# src/config.py -> src/ -> raiz do projeto
RAIZ = Path(__file__).resolve().parent.parent
PROMPTS_DIR = RAIZ / "prompts"
EVALS_DIR = RAIZ / "evals"
DOCS_DIR = RAIZ / "docs"

load_dotenv(RAIZ / ".env")

# ── Ollama Cloud ────────────────────────────────────────────────────────────
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")

# Host local — so usado se alguem prefixar um modelo com "local:".
# Este projeto roda 100% no Ollama Cloud; o caminho existe apenas por completude.
OLLAMA_HOST_LOCAL = os.environ.get("OLLAMA_HOST_LOCAL", "http://localhost:11434")

# O langchain_ollama le OLLAMA_HOST/OLLAMA_API_KEY do ambiente.
os.environ["OLLAMA_HOST"] = OLLAMA_HOST
if OLLAMA_API_KEY:
    os.environ["OLLAMA_API_KEY"] = OLLAMA_API_KEY

# ── Modelos e parametros (documentados em docs/relatorio_modelos.md) ────────
MODELO_PADRAO = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b")
# Segundo modelo do comparativo obrigatorio (§6). Mesma familia, 6x menor.
# ATENCAO: modelos pequenos (gemma3:4b, qwen3:8b) NAO existem no Ollama Cloud —
# so rodam localmente, e este projeto e 100% nuvem. Confira o que sua conta
# serve com: curl https://ollama.com/api/tags
MODELO_SECUNDARIO = os.environ.get("OLLAMA_MODEL_2", "gpt-oss:20b")

# Conversa: temperatura baixa — operador quer resposta estavel, nao criativa.
PARAMS_CHAT = {"temperature": 0.3, "top_p": 0.9, "num_predict": 1024}
# Extracao estruturada: temperatura 0 — o schema nao admite variacao.
# num_predict maior que na conversa porque o JSON carrega os campos de dado +
# a resposta em prosa dentro de `resposta_operador`. Descoberto no eval:
# com 768 o caso P2 (diagnostico de falha) truncava os ultimos 3 campos.
PARAMS_STRUCT = {
    "temperature": 0.0,
    "top_p": 1.0,
    "num_predict": int(os.environ.get("PARAMS_STRUCT_NUM_PREDICT", "1400")),
}

# ── Memoria ────────────────────────────────────────────────────────────────
MAX_TOKENS_HISTORICO = int(os.environ.get("MAX_TOKENS_HISTORICO", "800"))

# ── Prompt em producao ─────────────────────────────────────────────────────
PROMPT_VERSAO_PADRAO = os.environ.get("PROMPT_VERSAO", "v3")

_COMENTARIO_HTML = re.compile(r"<!--.*?-->", re.S)


def carregar_system_prompt(versao: str = PROMPT_VERSAO_PADRAO) -> str:
    """Le prompts/system_prompt_<versao>.md e remove o cabecalho de metadados.

    O cabecalho <!-- ... --> documenta a versao para humanos; nao deve consumir
    tokens do modelo. Por isso e removido antes de entrar na chain.
    """
    caminho = PROMPTS_DIR / f"system_prompt_{versao}.md"
    if not caminho.exists():
        disponiveis = sorted(p.stem for p in PROMPTS_DIR.glob("system_prompt_*.md"))
        raise FileNotFoundError(
            f"Prompt '{versao}' nao encontrado em {PROMPTS_DIR}. "
            f"Disponiveis: {disponiveis}"
        )
    texto = caminho.read_text(encoding="utf-8")
    return _COMENTARIO_HTML.sub("", texto).strip()


def checar_credenciais() -> tuple[bool, str]:
    """Retorna (ok, mensagem) — usado pelo CLI para falhar cedo e com clareza."""
    if not OLLAMA_API_KEY:
        return False, (
            "OLLAMA_API_KEY ausente. Crie um .env na raiz do projeto com:\n"
            "  OLLAMA_API_KEY=sua_chave\n"
            "  OLLAMA_MODEL=gpt-oss:120b\n"
            "O .env esta no .gitignore e nao pode ser commitado."
        )
    return True, "Credenciais carregadas."
