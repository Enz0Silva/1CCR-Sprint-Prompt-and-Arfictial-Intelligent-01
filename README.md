# ChargeGrid AI — Chatbot Inteligente para Eletropostos GoodWe

> **EV Challenge 2026 — FIAP x GoodWe · Sprint 03**
> Nucleo conversacional refatorado em **LangChain LCEL**, com memoria por sessao,
> saida estruturada validada e guardrails em duas camadas.

---

## Integrantes

| Nome Completo | RM |
|---------------|-----|
| Enzo Ricardo Silva | RM571333 |
| Eric Hernandes Penhalbell | RM570237 |
| Matheus Borges | RM574085 |
| Joao Guilherme Figueiredo | RM572697 |
| Ryan Luther | RM572993 |

---

## O que mudou nesta sprint

As Sprints 1 e 2 entregaram um CLI que falava direto com o Ollama Cloud: o
historico era uma lista Python que so crescia, a saida era sempre texto livre e
toda a defesa contra jailbreak vivia num unico bloco de prosa do system prompt.

A Sprint 03 reconstruiu esse nucleo:

| | Sprints 1/2 | Sprint 03 |
|---|---|---|
| Nucleo | `client.chat()` + lista de dicts | chain LCEL `prompt \| llm \| parser` |
| Memoria | lista global, sem teto | `RunnableWithMessageHistory` + janela de 800 tokens |
| Sessoes | uma so, global ao processo | N sessoes isoladas por `session_id` |
| Saida | string | string **ou** `ConsultaRecarga` validado (Pydantic v2) |
| System prompt | 1 `.txt` sem versao | v1/v2/v3 versionados, com ganho medido |
| Guardrails | so no texto do prompt | prompt **+** 2 camadas em codigo |
| Eval | 7 casos, avaliacao a olho | 19 casos com score automatico |

O escopo de produto e o mesmo: mesma persona, mesmo dominio. Esta sprint foi de
fundacao, nao de feature.

---

## Mapeamento Modulo 1 -> codigo

| Aula | Conteudo | Onde esta |
|------|----------|-----------|
| 01 | LCEL, ChatOllama, Output Parsers | `src/chain/builder.py` |
| 02 | Memoria conversacional com limite de tokens | `src/chain/memoria.py` |
| 03 | Structured output com Pydantic v2 | `src/schemas/ev.py` |
| 04 | Context engineering, XML tagging, tiktoken | `prompts/`, `evals/medir_prompts.py` |
| — | Seguranca e guardrails | `src/guardrails/` |

---

## Estrutura

```
chargegrid-ai/
├── prompts/
│   ├── system_prompt_v1.md      # baseline legado (Sprints 1/2)
│   ├── system_prompt_v2.md      # XML tagging
│   ├── system_prompt_v3.md      # producao
│   └── VERSOES.md               # tabela de versoes com ganho medido
├── src/
│   ├── config.py                # paths, env, modelos, parametros
│   ├── chain/
│   │   ├── builder.py           # chain LCEL + guardrails + structured output
│   │   ├── memoria.py           # MemoriaTokenBuffer por session_id
│   │   └── multi_provider.py    # bonus: matriz modelo x prompt
│   ├── schemas/ev.py            # ConsultaRecarga, SessaoRecarga, RelatorioFaturamento
│   ├── guardrails/
│   │   ├── scope_validator.py   # escopo GoodWe + dominios restritos
│   │   └── moderation.py        # jailbreak e prompt injection (entrada e saida)
│   ├── legado/chatbot_legado.py # versao Sprint 2 congelada, para o comparativo
│   └── backend/main.py          # CLI
├── evals/
│   ├── eval_set.json            # 19 casos
│   ├── run_eval.py              # roda o eval contra lcel ou legado
│   ├── comparar.py              # gera a tabela antes/depois
│   ├── medir_prompts.py         # tokens por versao de prompt
│   └── sprint3_results.json     # resultados (gerado)
├── docs/
│   ├── relatorio_evolucao.md    # fonte do relatorio
│   ├── relatorio_evolucao.pdf   # entregavel (gerado)
│   ├── gerar_relatorio_pdf.py
│   └── relatorio_modelos.md     # modelos e parametros
├── requirements.txt
├── .env.example
└── entrega_sprint.txt
```

---

## Instalacao

**Pre-requisito:** Python 3.11+ e uma chave do Ollama Cloud.

```bash
git clone https://github.com/Eoz0Silva/chargegrid-ai.git
cd chargegrid-ai

python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt     # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/Mac

copy .env.example .env      # Windows   (cp no Linux)
```

Abra o `.env` e preencha `OLLAMA_API_KEY`. O arquivo esta no `.gitignore`.

### No PyCharm

1. **Settings > Project > Python Interpreter** -> `.venv\Scripts\python.exe`
2. **Edit Configurations** -> *Working directory* = **raiz do projeto**
   (nao `src/backend/` — os imports sao a partir da raiz)
3. Rode `src/backend/main.py` com **Shift+F10**

---

## Uso

```bash
python src/backend/main.py
```

| Comando | Funcao |
|---------|--------|
| `/reset` | Limpa o historico da sessao atual |
| `/status` | Modelo, prompt e ocupacao da memoria |
| `/json <texto>` | Responde com saida estruturada validada |
| `/prompt <v>` | Troca a versao do system prompt (v1, v2, v3) |
| `/sessao <id>` | Troca de sessao (cada id tem memoria propria) |
| `/ajuda` | Lista os comandos |
| `/sair` | Encerra |

### Exemplo de memoria em 3+ turnos

```
Operador > O carregador 3 parou no meio da sessao. O que houve?
Operador > E quanto tempo leva para resolver?
Operador > De qual carregador eu estava falando mesmo?      <- so responde com historico
Operador > Abre um chamado para ele entao.
```

---

## Reproduzir as medicoes

Cada modulo roda sozinho para inspecao rapida:

```bash
python src/guardrails/moderation.py        # bateria de jailbreak (offline)
python src/guardrails/scope_validator.py   # bateria de escopo (offline)
python src/chain/memoria.py                # janela deslizante de tokens (offline)
python src/chain/builder.py                # 4 turnos reais contra o modelo
```

### Eval e comparativo antes/depois

```bash
python evals/medir_prompts.py                              # tokens por versao
python evals/run_eval.py --alvo legado --prompt v1 --tag sprint2
python evals/run_eval.py --alvo lcel   --prompt v3 --tag sprint3
python evals/comparar.py --antes sprint2 --depois sprint3
```

A ultima linha imprime a tabela obrigatoria do relatorio. Cole em
`docs/relatorio_evolucao.md` e gere o PDF:

```bash
python docs/gerar_relatorio_pdf.py
```

### Bonus multi-provider

```bash
python src/chain/multi_provider.py --modelos gpt-oss:120b gpt-oss:20b --prompts v1 v3
```

2 modelos x 2 prompts x 5 perguntas, com latencia e tokens por celula.

---

## Seguranca

- Credenciais so via `.env` (gitignored). Nenhuma chave no codigo ou no historico.
- **Guardrail de entrada** (`moderar_entrada`): jailbreak, troca de persona,
  vazamento de prompt, injection embutida em log, autoridade alegada e acesso
  indevido sao barrados **antes** da chamada ao modelo — sem resposta a vazar e
  sem token gasto.
- **Guardrail de escopo** (`validar_escopo`): separa dentro do escopo, fora do
  escopo e dominio restrito. Juridico, financeiro e seguranca eletrica recebem
  recusa que orienta profissional habilitado, nunca conselho.
- **Guardrail de saida** (`moderar_saida`): ultima barreira contra vazamento do
  system prompt e quebra de persona.
- **Schema como guardrail**: `field_validator` rejeita codigo de erro fora da base
  GoodWe e potencia acima do limite fisico da linha EV-C.

---

## Fora do escopo desta sprint

LangGraph, agentes, RAG, function calling novo, interface web e observabilidade
pertencem aos Modulos 3 e 4.

---

*EV Challenge 2026 — FIAP x GoodWe | Sprint 03 — Refactory conversacional em LangChain*
