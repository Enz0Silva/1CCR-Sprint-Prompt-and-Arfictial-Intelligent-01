# Modelo de Teste — ChargeGrid AI
## Sprint 1 | EV Challenge 2026 — FIAP x GoodWe

---

### P1 — Status geral dos carregadores

**PERGUNTA:**
"Quantos carregadores estão disponíveis agora no posto da Av. Paulista?"

**RESPOSTA ESPERADA:**
No posto da Av. Paulista, temos atualmente 8 carregadores ativos, dos quais:
- 5 disponíveis
- 2 em uso (sessão em andamento)
- 1 em falha (carregador #07 — erro de comunicação CAN bus)

Deseja que eu abra um chamado de manutenção para o carregador #07?

**CRITÉRIOS DE AVALIAÇÃO:**
- Apresentou status segmentado (disponível / em uso / falha)
- Identificou o carregador com problema e tipo de erro
- Ofereceu ação de encaminhamento ao final

---

### P2 — Diagnóstico de falha

**PERGUNTA:**
"O carregador #03 parou de carregar no meio da sessão. O que pode ter acontecido?"

**RESPOSTA ESPERADA:**
Com base no log da última sessão do carregador #03:
- Causa: Sobretensão detectada às 14h32 (pico de 253V)
- Impacto: Protocolo de proteção ativado, interrompendo a sessão
- Recomendação: Verificar estabilidade da rede elétrica do quadro.
  Se persistir, acionar suporte GoodWe (protocolo EVC-OVERVOLT-03).

Deseja registrar este incidente no histórico de manutenção?

**CRITÉRIOS DE AVALIAÇÃO:**
- Seguiu estrutura: causa -> impacto -> recomendação
- Citou protocolo técnico específico
- Confirmou antes de registrar ação

---

### P3 — Relatório de faturamento

**PERGUNTA:**
"Me dá um resumo do faturamento de março de 2026."

**RESPOSTA ESPERADA:**
Resumo de faturamento — março/2026:

| Métrica                | Valor        |
|------------------------|--------------|
| Total de sessões       | 1.247        |
| Energia total entregue | 18.340 kWh   |
| Receita bruta          | R$ 27.510,00 |
| Sessões via app GoodWe | 68%          |
| Sessões via RFID       | 32%          |
| Tempo médio de sessão  | 41 min       |

Comparado com fevereiro/2026: +12% em receita.
Deseja detalhar por carregador ou por tipo de veículo?

**CRITÉRIOS DE AVALIAÇÃO:**
- Apresentou dados em formato tabular organizado
- Incluiu comparativo com período anterior
- Ofereceu detalhamento adicional

---

### P4 — Gestão de potência / sobrecarga

**PERGUNTA:**
"Estamos com queda de energia parcial no quadro. Como posso reduzir
a carga sem desligar os carregadores?"

**RESPOSTA ESPERADA:**
Plano de Load Balancing de Emergência sugerido:

1. Reduzir para 50% da potência nos carregadores #01, #02 e #04
   (impacto mínimo no tempo de carga dos usuários)
2. Suspender aceite de novas sessões nos carregadores #05 e #06
3. Manter carregadores #07 e #08 (DC rápido) em operação normal

Resultado estimado: demanda reduzida de ~180 kW para ~95 kW.
Posso enviar o comando de ajuste via API GoodWe agora?

**CRITÉRIOS DE AVALIAÇÃO:**
- Propôs plano prático e numerado
- Estimou impacto em kW
- Solicitou confirmação antes de executar ação

---

### P5 — Dúvida técnica sobre protocolo

**PERGUNTA:**
"Qual protocolo de comunicação o GoodWe usa entre o backend e os
carregadores? Suporta OCPP 2.0.1?"

**RESPOSTA ESPERADA:**
Sim. Os carregadores GoodWe linha EV-C utilizam OCPP 1.6J (padrão atual).
O OCPP 2.0.1 está disponível via atualização de firmware para modelos a
partir de 2024, trazendo:
- Smart Charging nativo (Load Balancing automático)
- Autenticação ISO 15118 — Plug & Charge
- Melhor gestão de transações e relatórios de energia

A atualização leva aproximadamente 20 minutos por carregador via OTA.
Deseja que eu gere o roteiro de atualização?

**CRITÉRIOS DE AVALIAÇÃO:**
- Diferenciou versão atual (1.6J) da nova (2.0.1)
- Citou benefícios técnicos relevantes ao contexto
- Ofereceu próximo passo acionável
