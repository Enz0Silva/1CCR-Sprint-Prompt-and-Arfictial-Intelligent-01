# ChargeGrid AI — Chatbot Inteligente para Eletropostos GoodWe

> Projeto desenvolvido para o **EV Challenge 2026** — FIAP x GoodWe
> Contexto: **ChargeGrid Intelligence** (operador comercial / técnico)

---

## Integrantes

| Nome Completo               | RM       |
|-----------------------------|----------|
| Enzo Ricardo Silva          | RM571333 |
| Eric Hernandes Penhalbell   | RM570237 |
| Murilo Ignacio              | RM573621 |
| Matheus Borges              | RM574085 |
| João Guilherme Figueiredo   | RM572697 |
| Ryan Luther                 | RM572993 |

---

## Problema Abordado

Os eletropostos comerciais equipados com hardware GoodWe enfrentam lacunas críticas
na gestão operacional:

- **Billing e registro de ciclos**: ausência de mecanismo integrado para faturar
  automaticamente sessões por usuário, veículo ou contrato e auditar o histórico
  de ciclos de carga de forma confiável
- **Orquestração de potência**: sem controle centralizado para redistribuir carga
  entre múltiplos carregadores simultâneos, causando sobrecarga ou subutilização
- **Acesso operacional em campo**: operadores técnicos não possuem canal conversacional
  para consultar status, diagnosticar falhas e agir sobre dados em tempo real
- **Comunicação de status**: ausência de alertas proativos e relatórios consolidados
  para tomada de decisão rápida

Esse conjunto de lacunas — chamado de **ChargeGrid Intelligence** pela GoodWe — resulta
em ineficiência operacional, perda de receita e dificuldade de manutenção preventiva.

---

## Proposta do Chatbot

O **ChargeGrid AI** é um chatbot operacional com IA generativa voltado para operadores
comerciais e técnicos de eletropostos equipados com hardware GoodWe.

### Persona Principal
**Operador Comercial / Técnico de Campo** — profissional responsável por monitorar
o funcionamento dos carregadores, responder a falhas, gerar relatórios e tomar
decisões sobre distribuição de carga. Suas dores específicas:
- Precisa de dados consolidados sem acessar múltiplos sistemas
- Toma decisões críticas em campo com informação incompleta
- Não tem canal direto para diagnóstico técnico rápido de equipamentos GoodWe

### O que o chatbot responde
- Status em tempo real dos eletropostos (disponível, ocupado, em falha)
- Histórico de sessões de carga por carregador ou período
- Alertas de sobrecarga e sugestões de redistribuição de potência
- Relatórios de faturamento e consumo energético
- Diagnóstico de falhas e orientações de manutenção
- Dúvidas técnicas sobre equipamentos GoodWe e protocolos OCPP

---

## Tecnologias

| Tecnologia      | Função                        | Prós                                              | Contras                                      |
|-----------------|-------------------------------|---------------------------------------------------|----------------------------------------------|
| Ollama Cloud    | Motor de LLM gerenciado       | Gratuito para uso, sem hardware local, baixa latência | Requer API Key, dependência de conexão       |
| gpt-oss:120b    | Modelo de linguagem principal | Open-source 120B, ótimo em PT-BR, contexto amplo  | Modelo grande, latência maior que 8B         |
| Python 3.11+    | Backend do chatbot            | Ecossistema amplo, padrão em IA                   | Performance inferior a Go/Rust               |
| ollama (lib)    | Cliente Python para Ollama    | API simples, suporta streaming e chat history     | Documentação ainda em evolução               |
| python-dotenv   | Gerenciamento de variáveis    | Seguro, padrão de mercado                         | Apenas para ambiente local                   |

### Por que Ollama Cloud e não outras opções?

| Critério               | Ollama Cloud    | Groq API        | OpenAI GPT-4    | Gemini          |
|------------------------|-----------------|-----------------|-----------------|-----------------|
| Custo                  | Gratuito        | Gratuito (limite) | Pago          | Gratuito (limite) |
| Qualidade PT-BR        | Excelente       | Boa             | Excelente       | Boa             |
| Janela de contexto     | 128k tokens     | 8k tokens       | 128k tokens    | 1M tokens       |
| Modelos open-source    | Sim             | Sim             | Não             | Não             |
| Privacidade dos dados  | Alta            | Média           | Baixa           | Baixa           |
| Latência               | Média           | Muito baixa     | Média           | Média           |

Ollama Cloud foi escolhido por oferecer acesso gratuito ao modelo `gpt-oss:120b`
(open-source de 120 bilhões de parâmetros), excelente qualidade em português e
janela de contexto ampla — essencial para manter memória conversacional rica.

---

## Estrutura do Repositório

\`\`\`
chargegrid-ai/
├── README.md
├── .env.example
├── .gitignore
├── docs/
│   ├── fluxograma_chargegrid_ai.svg
│   ├── modelo_de_teste.md
│   └── resultados_testes.md       ← NOVO Sprint 2
├── prompts/
│   └── system_prompt.txt
├── src/
│   └── backend/
│       ├── chatbot.py
│       ├── main.py
│       └── requirements.txt
└── entrega_sprint.txt
\`\`\`

---

## Pré-requisitos

1. **Python 3.11+** instalado
2. **API Key do Ollama Cloud** — obtenha em https://ollama.com

---

## Configuração do Ambiente

### 1. Clonar o repositório
\`\`\`bash
git clone https://github.com/Enz0Silva/1CCR-Sprint-Prompt-and-Arfictial-Intelligent-01.git
cd 1CCR-Sprint-Prompt-and-Arfictial-Intelligent-01
\`\`\`

### 2. Criar o arquivo .env
\`\`\`bash
cp .env.example .env
\`\`\`

Conteúdo do `.env`:
\`\`\`
OLLAMA_API_KEY=sua_chave_aqui
OLLAMA_MODEL=gpt-oss:120b
\`\`\`

O arquivo `.env` está no `.gitignore` e nunca deve ser commitado.

### 3. Criar ambiente virtual e instalar dependências
\`\`\`bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install ollama python-dotenv
\`\`\`

---

## Como Rodar no PyCharm

1. **Edit Configurations** → selecione o interpretador do `.venv`
2. No campo **"Paths to .env files"**, aponte para o `.env` na raiz
3. Abra `src/backend/main.py` e pressione **Shift+F10**

Pelo terminal:
\`\`\`bash
cd src/backend
python main.py
\`\`\`

---

## Comandos do CLI

| Comando   | Função                              |
|-----------|-------------------------------------|
| `/reset`  | Limpa o histórico de conversa       |
| `/status` | Exibe modelo e URL do Ollama        |
| `/ajuda`  | Lista os comandos disponíveis       |
| `/sair`   | Encerra o chatbot                   |

---

## Memória de Contexto

O chatbot mantém histórico completo da conversa em memória durante a sessão.
Cada mensagem enviada ao Ollama inclui todas as trocas anteriores, permitindo
diálogos contínuos e coerentes sem necessidade de repetir contexto.

O histórico é resetado ao digitar `/reset` ou reiniciar o programa.

---

## Modelo de Teste e Resultados

- Modelo de teste: `docs/modelo_de_teste.md` (7 casos, incluindo fora do escopo e jailbreak)
- Resultados documentados: `docs/resultados_testes.md`

**Resumo: 6 de 7 casos com avaliação Adequada.**

---

## Segurança

- API Key carregada via variável de ambiente, nunca exposta no código
- `.env` no `.gitignore` — nunca commitado no repositório
- Modelo segue restrições rígidas: não inventa dados, recusa jailbreak, redireciona fora do escopo

---

*EV Challenge 2026 — FIAP x GoodWe | Sprint 2 — Desenvolvimento e Entrega*