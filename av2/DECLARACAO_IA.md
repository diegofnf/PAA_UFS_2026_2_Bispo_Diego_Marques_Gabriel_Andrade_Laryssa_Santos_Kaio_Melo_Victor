# Declaração de uso de IA generativa — AV2

**Responsáveis pelas etapas documentadas:** Victor Melo (Etapa 5) e Laryssa Barbosa de Andrade (Etapa 6)
**Data:** 03/11/2026
**Ferramenta:** GitHub Copilot no VS Code, com assistente baseado em Copilot SDK.
**Modelo:** selecionado na própria sessão do Copilot; a equipe deve registrar
aqui o identificador exibido no seletor de modelos antes da entrega.

## 1. Finalidade

A IA foi usada como apoio para:

- ler os artefatos da AV2 e identificar a interface entre as Etapas 1–4 e a Etapa 5;
- discutir a modelagem do orçamento de tokens e a separação entre `W` e janela da LLM;
- gerar rascunhos de código, testes e documentação;
- revisar complexidade, riscos e inconsistências;
- apoiar a auditoria dos resultados experimentais.

A IA **não** foi usada para inventar resultados, substituir a execução dos
scripts ou declarar corretude sem verificação.

## 2. Prompts relevantes (resumo)

1. “A Etapa 5 tem como objetivo integrar os resultados dos algoritmos de seleção
   de chunks a um fluxo compatível com LLMs…”
2. “Leia a atividade na branch av2 e veja o que mudou no plano.”
3. “Implemente na branch av2, com janelas de 1.024 a 16.384.”
4. “Faça uma auditoria completa: requisitos, código, complexidade, bugs e
   autoavaliação.”
5. “Execute o notebook em cópia limpa, commite na av2 e atualize as evidências.”

## 3. Sugestões aproveitadas

- Estrutura de `montar_cenario`, `BlocoFonte` e `ResultadoCenario`.
- Deduplicação por intervalos de palavras, preservando os intervalos reais.
- Matriz de 160 execuções e testes sintéticos/integrados.
- Política de reservar 190 tokens fixos, 512 para resposta e 64 de segurança.

## 4. Sugestões corrigidas ou rejeitadas

| Sugestão inicial | Decisão | Motivo |
|---|---|---|
| Usar heurística de tokens como padrão | Rejeitada para a AV2 | A AV2 fixa `tiktoken==0.14.0`, `cl100k_base`, `encode_ordinary` |
| Tratar `W` como janela da LLM | Rejeitada | `W` é a soma dos `w_i`; instruções, resposta e segurança são custos adicionais |
| Usar `gpt-4o-mini` como modelo de referência | Corrigida | `gpt-4o` usa `o200k_base`; o padrão passou a `gpt-4-turbo` (`cl100k_base`) |
| Taxas de latência fixas em 2.000/60 | Corrigida | As taxas viraram parâmetros do CLI |
| Dedupe sempre reportado como economia | Corrigida | Separados economia potencial e aplicada |
| “O ajustado nunca estoura” | Corrigida | Vale para janelas ≥1.024; abaixo de 766 tokens nem o prompt fixo cabe |

## 5. Erros identificados e verificações

- `w_i` foi conferido contra `encode_ordinary` nos 182 chunks (74.055 tokens).
- O prompt final foi recontado; a concatenação altera tokens nas bordas.
- Blocos removidos no reparo final passaram a ser contados.
- O ponto de entrada oficial `av2/integrar_contexto.py` foi testado.
- A suíte da AV2 foi executada: **92 testes aprovados** (34 da preparação, 10 do
  baseline guloso, 9 da programação dinâmica, 5 da corretude e 34 da Etapa 5).
- Os artefatos da Etapa 5 foram regenerados em clone limpo no commit `5b0fe1d`
  para que a evidência registre `arvore_suja_antes_gravar = false`.
- Nenhuma chamada a LLM foi feita nesta etapa.

## 6. Limitações declaradas

A IA pode produzir código plausível, mas não garante corretude. Toda a
implementação foi submetida a testes automatizados e deve ser revisada pelos
autores antes da entrega. A avaliação da qualidade das respostas geradas por
LLM não foi executada por ausência de modelo/credencial definidos no repositório.

## 7. Apoio à Etapa 6

Na etapa de métricas, a IA foi usada como apoio à leitura do enunciado, à
revisão da matriz experimental e à organização da documentação. A execução do
benchmark, os valores de tempo e memória, os casos de teste e os gráficos foram
gerados pelo script `av2/medir_experimentos.py` e conferidos nos artefatos
versionados. Não foram inventados resultados nem substituída a execução local.
