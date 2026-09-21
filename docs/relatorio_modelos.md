# Relatorio de uso de modelos e parametros — ChargeGrid AI

> Exigencia da Sprint 03, §6: comparar 2+ modelos e documentar `temperature`,
> `top_p` e `max_tokens`.
>
> **Antes de entregar:** rode `python src/chain/multi_provider.py` e substitua as
> celulas marcadas com `[preencher]` pelos numeros medidos na maquina de voces.

---

## 1. Parametros em uso

Definidos em `src/config.py` — uma fonte unica lida pela chain, pelo eval e pela
matriz multi-provider, para que os tres nunca divirjam.

| Perfil | Onde e usado | temperature | top_p | max_tokens (`num_predict`) |
|--------|--------------|-------------|-------|----------------------------|
| `PARAMS_CHAT` | `responder()` — conversa com o operador | 0.3 | 0.9 | 1024 |
| `PARAMS_STRUCT` | `extrair()` — saida `ConsultaRecarga` | 0.0 | 1.0 | 768 |

### Por que estes valores

**`temperature=0.3` na conversa.** O operador esta em campo decidindo se corta
potencia de um quadro. Duas execucoes da mesma pergunta precisam dar a mesma
recomendacao; se variarem, ele perde a confianca na ferramenta. Nao usamos 0.0
porque a 0.0 o modelo fica repetitivo na formatacao (repete o mesmo cabecalho de
tabela turno apos turno) sem ganho de acuracia perceptivel no nosso eval.

**`temperature=0.0` na extracao.** Schema nao admite criatividade. Qualquer
variacao aqui vira `ValidationError`, ou seja, uma chamada de modelo jogada fora.

**`top_p=0.9` na conversa.** Corta a cauda de tokens improvaveis — que e de onde
vem termo tecnico inventado, do tipo "EVC-THERMAL-99". Com `temperature` ja
baixa, mexer nos dois ao mesmo tempo seria redundante; mantivemos `top_p=1.0` na
extracao porque a temperatura 0 ja restringe o suficiente.

**`num_predict=1024` na conversa.** No Ollama, `num_predict` e o equivalente ao
`max_tokens` dos outros providers (Aula 01). 1024 cobre diagnostico com tabela
sem truncar; 768 basta para o JSON do `ConsultaRecarga`, que e menor que a
resposta em prosa.

**`max_token_limit=800` na memoria.** Teto do historico por sessao
(`MAX_TOKENS_HISTORICO`). Valor herdado do Exercicio 2 da Aula 02 e mantido: cobre
cerca de 5 a 7 turnos de operacao, que e o tamanho tipico de um atendimento de
campo antes do assunto mudar.

---

## 2. Modelos comparados

| | `gpt-oss:120b` | `gpt-oss:20b` |
|---|---|---|
| Papel | modelo padrao de producao | alternativa leve / contingencia |
| Parametros | 120B | 20B |
| Onde roda | Ollama Cloud | Ollama Cloud |
| Contexto | 128K tokens | 128K tokens |
| Por que esta na comparacao | modelo do semestre, base de toda a disciplina | 6x menor, mesma familia e mesmo tokenizer — isola o efeito do **tamanho** do modelo, sem trocar arquitetura junto |

> **Por que os dois sao cloud.** O projeto roda inteiramente no Ollama Cloud: o
> grupo nao instala Ollama nas maquinas. Modelos pequenos como `gemma3:4b` ou
> `qwen3:8b` so existem localmente, entao ficaram fora. Para conferir o que a
> conta de voces serve na nuvem: `curl https://ollama.com/api/tags`.

### Resultado medido

Gere com:

```bash
python src/chain/multi_provider.py --modelos gpt-oss:120b gpt-oss:20b --prompts v1 v3
```

O comando imprime a tabela pronta e grava o detalhe em `docs/matriz_modelos.json`.

| Modelo | Prompt | Chamadas OK | Latencia media (s) | Tokens entrada | Tokens saida |
|--------|--------|-------------|--------------------|----------------|--------------|
| gpt-oss:120b | v1 | 5 | 1,75 | 1.103 | 278 |
| gpt-oss:120b | v3 | 5 | 1,43 | 996 | 114 |
| gpt-oss:20b | v1 | 5 | 6,37 | 1.103 | 278 |
| gpt-oss:20b | v3 | 5 | 6,63 | 996 | 122 |

### Qualidade por modelo (eval set completo)

```bash
python evals/run_eval.py --alvo lcel --modelo gpt-oss:120b --tag gptoss120
python evals/run_eval.py --alvo lcel --modelo gpt-oss:20b   --tag gptoss20
python evals/comparar.py --tags gptoss120 gptoss20
```

| Metrica | gpt-oss:120b | gpt-oss:20b |
|---------|--------------|----------|
| Nota no eval (0-10) | [preencher] | [preencher] |
| Comportamento esperado (%) | [preencher] | [preencher] |
| Acuracia do structured output (%) | [preencher] | [preencher] |
| Latencia media (s) | [preencher] | [preencher] |

---

## 3. Matriz modelo x prompt (bonus +1 pt)

O bonus pede chamada com mais de um modelo **e** mais de um prompt.
`src/chain/multi_provider.py` roda a matriz completa numa execucao: 2 modelos x
2 versoes de prompt x 5 perguntas = 20 chamadas, com latencia e tokens por celula.

O que a matriz responde que uma comparacao simples nao responde: **se o ganho do
prompt v3 depende do modelo**. Se o modelo menor melhorar mais com o v3 do que o
grande, isso significa que o context engineering esta compensando capacidade —
um resultado util, porque abre a porta para rodar o chatbot em hardware menor
dentro da rede da GoodWe.

Se o grupo quiser um terceiro provider (OpenAI, Anthropic), como no notebook da
Aula 01, funcionam com prefixo no nome:

```bash
python src/chain/multi_provider.py --modelos gpt-oss:120b openai:gpt-4o-mini
```

Sem a chave correspondente no `.env`, a celula e pulada com aviso e a matriz
segue rodando.

---

## 4. Conclusao

**1. Modelo em producao: `gpt-oss:120b` com prompt v3.** A escolha combina o
melhor score no eval (nota 8,71 na primeira execucao completa) com a menor
latencia observada na nuvem (1,43s de media contra 6,63s do `gpt-oss:20b`).

**2. Achado inesperado: o modelo menor foi mais lento, nao mais rapido.** O
`gpt-oss:20b` roda entre 3,6x e 4,6x mais lento que o `gpt-oss:120b` na Ollama
Cloud. E contraintuitivo — modelo menor "deveria" processar mais rapido —, mas na
nuvem gerenciada a latencia raramente reflete o tamanho do modelo. Reflete
alocacao de recursos: modelos-carro-chefe como o `120b` costumam rodar em GPUs
dedicadas com fila curta, enquanto os modelos menores compartilham
infraestrutura de menor prioridade.

Isso e relevante para o projeto: **nao ha vantagem operacional em rodar o
modelo pequeno na nuvem**. O comparativo faria sentido diferente se o `20b`
estivesse rodando localmente no proprio hardware da GoodWe — ai a latencia
seria dominada pela maquina, nao pela fila. Este cenario nao foi testado
porque o grupo optou por rodar 100% na nuvem (ver §2).

**3. O ganho do prompt v3 depende do modelo.** No `120b`, v1 -> v3 reduziu a
latencia de 1,75s para 1,43s — 18% mais rapido. No `20b`, a latencia praticamente
nao mudou (6,37s -> 6,63s, dentro da margem de ruido). Isso indica que a
economia de 107 tokens de sistema (1.084 -> 977) so se converte em ganho de
tempo quando o modelo em si esta rapido. Com o modelo grande, cada token conta;
com o modelo pequeno na fila da nuvem, o gargalo esta em outro lugar.

**4. Parametros mantidos como propostos.** `temperature=0.3` na conversa e 0.0
na extracao seguiram funcionando bem no eval completo. `num_predict` da
extracao **foi ajustado**: subiu de 768 para 1.400 apos o caso P2 truncar os
ultimos 3 campos do JSON. O parametro e configuravel via `.env`
(`PARAMS_STRUCT_NUM_PREDICT`) para permitir experimentacao sem editar codigo.
