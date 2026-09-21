# Tabela de versoes do system prompt — ChargeGrid AI

> Exigencia da Sprint 03, §6: "tabela de versoes com o que mudou, por que e o ganho medido".
>
> **Tokens: medidos** com `tiktoken` (encoding `cl100k_base`), reproduzivel com
> `python evals/medir_prompts.py`. A coluna de **aderencia** ainda precisa ser
> preenchida — ela depende de rodar o eval contra o modelo:
>
> ```bash
> python evals/run_eval.py --prompt v1 --tag v1
> python evals/run_eval.py --prompt v2 --tag v2
> python evals/run_eval.py --prompt v3 --tag v3
> python evals/comparar.py --tags v1 v2 v3
> ```

## Versoes

| Versao | Data | O que mudou | Por que | Tokens (tiktoken) | Aderencia no eval |
|--------|------|-------------|---------|-------------------|-------------------|
| v1 | 03/08 | Prompt herdado das Sprints 1/2. Prosa corrida, 9 blocos em maiuscula, instrucoes criticas no meio do texto. | Baseline. Nao foi alterado — serve de referencia para medir o ganho. | **1084** (baseline) | preencher |
| v2 | 24/08 | Reescrito com XML tagging: `<persona>`, `<capacidades>`, `<base_conhecimento>`, `<formato>`, `<escalada_humana>`, `<critico>`. Redundancia removida (listas de capacidade e base tecnica compactadas em linhas). Regras criticas movidas para a ultima borda. | Aula 04: em prosa longa o modelo prioriza o inicio e "esquece" o meio (context rot / Lost in the Middle). O system prompt entra em **todos** os turnos, entao cada token economizado se multiplica pelo numero de turnos da sessao. | **677** (**-38%**) | preencher |
| v3 | 14/09 | v2 + bloco `<dominios_restritos>` (juridico, financeiro, seguranca eletrica) com formato de recusa em 3 passos; item 4 do `<critico>` reescrito para tratar texto do usuario/log/anexo como dado e nao como instrucao. | No eval da v2, os casos de dominio restrito eram respondidos como duvida tecnica comum, sem orientar profissional habilitado (perda direta no bloco C da rubrica). O reforco anti-injection fecha a variante "autoridade alegada" (usuario dizendo ser gestor/dev GoodWe). | **977** (**-10%**) | preencher |

### Custo projetado por sessao

Como o system prompt entra em todos os turnos, o valor se multiplica:

| Versao | Tokens/turno | 10 turnos | Diferenca vs v1 em 10 turnos |
|--------|--------------|-----------|------------------------------|
| v1 | 1084 | 10.840 | — |
| v2 | 677 | 6.770 | -4.070 |
| v3 | 977 | 9.770 | -1.070 |

### O que esses numeros revelam

O XML tagging sozinho (v1 -> v2) corta **38%**. Mas a v3 devolve 300 tokens ao
reintroduzir o bloco `<dominios_restritos>`, e o ganho liquido cai para **10%**.

Isso nao invalida a decisao — evidencia o trade-off. Tres quartos da economia do
context engineering foram gastos comprando aderencia em dominio restrito. O
criterio de escolha foi aderencia primeiro, token depois: 300 tokens por turno e
barato perto do custo de o assistente dar conselho juridico ou orientar
intervencao em quadro energizado.

A leitura errada seria "refatorar prompt sempre economiza token". A leitura certa
e que refatoracao libera orcamento de contexto — e o que voce faz com esse
orcamento e uma segunda decisao, separada e explicita.

O `comparar.py` imprime a tabela pronta para colar aqui e no relatorio de evolucao.

## Decisoes de prompt registradas

- **Por que ASCII puro.** Herdado da Sprint 2 e mantido de proposito: acento e cedilha
  custam tokens extras no BPE e quebram o console do Windows (cp1252) usado pelo grupo.
  A instrucao fica em `<formato>`, nao repetida em cada secao.
- **Por que v3 nao e a mais curta.** v2 e 300 tokens menor, mas perde no bloco C
  da rubrica. O criterio de escolha foi aderencia primeiro, token depois — 300
  tokens por turno e um preco aceitavel para nao dar conselho juridico ou eletrico.
- **Por que `<critico>` fica no fim.** Exercicio 1 da Aula 04: a mesma regra colocada
  no meio do bloco tem aderencia menor do que na borda. Persona no inicio, regra dura no fim.
- **O que nao foi para o prompt.** Deteccao de jailbreak e de escopo tambem roda em
  codigo (`src/guardrails/`), antes e depois do LLM. Prompt e defesa probabilistica;
  guardrail em codigo e deterministico. As duas camadas juntas, nunca so uma.
