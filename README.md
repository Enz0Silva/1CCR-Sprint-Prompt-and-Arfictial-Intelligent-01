# ChargeGrid AI — Chatbot Inteligente para Eletropostos GoodWe

> Projeto desenvolvido para o **EV Challenge 2026** — FIAP x GoodWe
> Contexto: **ChargeGrid Intelligence** (operador comercial / técnico)

---

## Integrantes

| Nome    | RM       |
|---------|----------|
| Enzo    | RM571333 |
| Eric    | RM570237 |
| Murilo  | RM573621 |
| Matheus | RM574085 |
| João    | RM572697 |
| Ryan    | RM572993 |

---

## Problema Abordado

Os eletropostos comerciais atualmente carecem de mecanismos integrados para:

- Orquestrar potência entre múltiplos carregadores simultâneos
- Registrar ciclos de carga de forma auditável e histórica
- Faturar automaticamente sessões por usuário, veículo ou contrato
- Comunicar status em tempo real para operadores e técnicos

Esse conjunto de lacunas — chamado de **ChargeGrid Intelligence** pela GoodWe — resulta
em ineficiência operacional, perda de receita e dificuldade de manutenção. Não existe
hoje um canal conversacional que permita ao operador consultar, diagnosticar e agir
sobre esses dados de forma natural e imediata.

---

## Proposta do Chatbot

O **ChargeGrid AI** é um chatbot operacional com IA generativa voltado para **operadores
comerciais e técnicos de eletropostos** equipados com hardware GoodWe.

### Persona Principal
**Operador Comercial / Técnico de Campo** — pessoa responsável por monitorar o
funcionamento dos carregadores, responder a falhas, gerar relatórios e tomar
decisões sobre distribuição de carga.

### O que o chatbot responde
- Status em tempo real dos eletropostos (disponível, ocupado, em falha)
- Histórico de sessões de carga por carregador ou período
- Alertas de sobrecarga e sugestões de redistribuição de potência
- Relatórios de faturamento e consumo energético
- Diagnóstico de falhas e orientações de manutenção
- Dúvidas técnicas sobre equipamentos GoodWe e protocolos OCPP

### Justificativa da Escolha do Contexto
O contexto **comercial/técnico** foi escolhido por apresentar maior complexidade
operacional e maior impacto no negócio. Operadores tomam decisões críticas em campo
sem acesso fácil a dados consolidados — o chatbot resolve esse gap funcionando como
um painel inteligente conversacional.

---

## Tecnologias Selecionadas

| Tecnologia           | Função                             | Justificativa                                              |
|----------------------|------------------------------------|------------------------------------------------------------|
| Groq API             | Modelo principal de linguagem      | API gratuita de alta velocidade, suporta modelos como LLaMA 3 e Mixtral com baixa latência |
| LLaMA 3 (70B)        | LLM via Groq                       | Modelo open-source com ótimo desempenho em português e contexto técnico |
| Python 3.11+         | Backend do chatbot                 | Padrão em IA; amplo ecossistema de libs                    |
| FastAPI              | API REST para o backend            | Leve, assíncrono, ideal para streaming de respostas        |
| React + Tailwind CSS | Interface frontend                 | Componentização eficiente para UI operacional              |
| PostgreSQL           | Banco de dados                     | Confiabilidade e queries complexas para relatórios         |
| Docker               | Containerização                    | Portabilidade — inclui backend + frontend                  |

### Por que Groq e não outras APIs (OpenAI, Claude, Gemini)?
O Groq foi escolhido por oferecer um **plano gratuito generoso** com altíssima velocidade
de inferência (LPU — Language Processing Unit), ideal para respostas rápidas em ambiente
operacional. Além disso, é compatível com o padrão OpenAI, facilitando a integração.
Os modelos disponíveis (LLaMA 3, Mixtral) são open-source e apresentam excelente
desempenho em português e contexto técnico.

---

## Fluxograma de Funcionamento

Ver arquivo: `docs/fluxograma_chargegrid_ai (1).svg`

**Resumo do fluxo:**
1. Operador digita mensagem no frontend React
2. Frontend envia POST para o backend FastAPI
3. FastAPI consulta PostgreSQL (logs, sessões, histórico)
4. Backend monta o contexto: system prompt + histórico + dados + mensagem
5. Backend chama a Groq API via HTTP (Authorization: Bearer API_KEY)
6. Groq processa o prompt na nuvem e retorna a resposta
7. Resposta é enviada ao frontend
8. Log da interação é salvo no PostgreSQL

---

## Configuração do Ambiente

### Variáveis de Ambiente (`.env`)

```env
# Groq API
GROQ_API_KEY=sua-chave-aqui
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=llama3-70b-8192

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/chargegrid

# Backend
API_PORT=8000
```

### Como obter a chave Groq
1. Acesse https://console.groq.com
2. Crie uma conta gratuita
3. Gere uma API Key em "API Keys"
4. Cole no `.env`

### Como rodar

```bash
# Instalar dependências
pip install -r src/backend/requirements.txt

# Rodar o backend
uvicorn src.backend.main:app --reload

# Testar
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Qual o status dos carregadores?"}'
```

---

## System Prompt (Contexto-Base)

Ver arquivo: `prompts/system_prompt.txt`

---

## Modelo de Teste

Ver arquivo: `docs/modelo_de_teste.md`

---

## Estrutura do Repositório

```
chargegrid-ai/
├── README.md
├── .env
├── docs/
│   ├── fluxograma_chargegrid_ai.svg
│   └── modelo_de_teste.md
├── src/
│   ├── backend/
│   │   ├── main.py
│   │   ├── chatbot.py
│   │   └── requirements.txt
│   └── frontend/
│       ├── App.jsx
│       └── components/
│           └── ChatWindow.jsx
├── prompts/
│   └── system_prompt.txt
├── docker-compose.yml
└── .env.example
```

---

*Projeto desenvolvido no contexto do EV Challenge 2026 — FIAP x GoodWe*
*Sprint 1 — Exploração e Planejamento*