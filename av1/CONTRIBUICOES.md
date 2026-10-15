# Contribuições individuais dos integrantes

Documento exigido pelo **item 10 da Seção 10** ("relação de todos os participantes
da equipe com as respectivas contribuições para esta atividade") e pelo **item 8
da Seção 9** (contribuição individual na declaração de uso de IA).

---

## Equipe

| Nome | Papel nesta atividade |
|---|---|
| **Diego Bispo** | Dados, corpus e orquestração do *pipeline* |
| **Gabriel Marques** | Busca lexical e ordenação (Etapa 4) |
| **Laryssa Andrade** | Implementação do *pipeline* (Etapas 1–6) e aplicação web |
| **Kaio Santos** | *Chunking*, busca lexical e casos de teste |
| **Victor Melo** | Análise assintótica (Etapa 7), resultados, infraestrutura e integração |

Total de **5 integrantes**, dentro da faixa de 5 a 7 exigida pela Seção 16.

---

## Método de apuração

As contribuições versionadas foram apuradas diretamente do histórico Git
(`git log --name-status`, `git log --numstat`, `git shortlog`), com dois
cuidados metodológicos:

1. **Identidades consolidadas.** O histórico registra mais de uma assinatura por
   integrante, e elas foram unificadas para não fragmentar a contagem:

   | Integrante | Identidades no histórico |
   |---|---|
   | Diego Bispo | `diegofnf@users.noreply.github.com` e `145767830+diegofnf@users.noreply.github.com` |
   | Kaio Santos | `kaioc89@gmail.com` (assina também como `kaio` e `Kaio`) |
   | Laryssa Andrade | `laryssabarbosadeandrade@Laptop-de-Laryssa.local` |

2. **Contagem por entrega, não por linha.** **Não** se usa o número de linhas
   adicionadas/removidas como medida de contribuição, porque a maior parte do
   volume do repositório são **artefatos gerados** (chunks, índice invertido,
   relatórios JSON, PNGs e CSVs), cujo tamanho não mede esforço intelectual.
   A tabela abaixo registra **etapas concluídas e artefatos produzidos**.

**Limitação declarada:** posse de arquivo não implica autoria exclusiva. O
trabalho foi iterativo e todos os integrantes revisaram artefatos uns dos
outros; a atribuição abaixo indica o **responsável principal** por cada frente,
não uma separação estanque de trabalho.

---

## Contribuição por integrante

### Diego Bispo — 26 commits

| Frente | Evidência |
|---|---|
| Corpus e dados (`3_dados/`) | 9 alterações em `3_dados/` e nas versões anteriores (`dados/`); artefatos `catalogo_documentos.json`, `documentos_extraidos.json`, `documentos_normalizados.json`, `relatorio_processamento.json` |
| Índice invertido (`5_indexacao/`) | Construção e versionamento do `indice_invertido.json` e do `relatorio_indexacao.json` |
| Orquestração | 7 commits em `orquestrador_pipeline.ipynb` |
| Documentação | 17 commits em `README.md` — o arquivo com maior número de revisões do repositório |

### Gabriel Marques — 8 commits

| Frente | Evidência |
|---|---|
| Etapa 4 — busca e ordenação | 1 commit direto em `1_scripts/4_buscar_e_ordenar.py` |
| Artefatos da Etapa 4 | Criação de `6_busca_lexical/candidatos_ordenados.json`, `candidatos_topk.json` e `relatorio_ordenacao.json` |
| Revisão | Alterações em `README.md` e `orquestrador_pipeline.ipynb` |

### Laryssa Andrade — 2 commits

| Frente | Evidência |
|---|---|
| Implementação do *pipeline* (Etapas 1 a 6) | Commits que introduziram `1_scripts/1_processar_documentos.py`, `2_gerar_chunks.py`, `3_construir_indice_invertido.py`, `4_buscar_e_ordenar.py`, `5_experimentar.py`, `6_gerar_graficos.py` |
| Casos de teste | Introdução de `1_scripts/test_etapa_4.py` (a suíte de 14 testes) |
| Artefatos de dados | `4_chunks/chunks.json`, `4_chunks/relatorio_chunking.json`, `5_indexacao/*` |
| Aplicação web (`src/`) | 13 commits na camada React/Vite e em `public/` |
| Infraestrutura de *deploy* | Introdução de `.github/workflows/deploy-vercel.yml` |

> A contagem de commits é baixa porque o trabalho foi concentrado em poucos
> commits grandes — o oposto do padrão de Victor e Diego. O critério de
> "etapas concluídas" reflete melhor o volume: **as Etapas 1 a 6 foram
> introduzidas por essa frente de trabalho**, o que inclui o núcleo algorítmico
> do projeto.

### Kaio Santos — 5 commits

| Frente | Evidência |
|---|---|
| Etapa 2 — *chunking* | Criação de `4_chunks/chunks.json` e `4_chunks/relatorio_chunking.json` e alterações em `1_scripts/2_gerar_chunks.py` |
| Etapa 4 — busca | Criação dos artefatos das duas configurações: `6_busca_lexical/candidatos_linear.json`, `candidatos_indexada.json`, `relatorio_busca_linear.json`, `relatorio_busca_indexada.json` |
| Testes | Coautoria de `1_scripts/test_etapa_4.py` |
| Orquestração e documentação | 3 commits em `orquestrador_pipeline.ipynb` e 3 em `README.md` |

### Victor Melo — 37 commits

| Frente | Evidência |
|---|---|
| Etapa 7 — análise assintótica | Criação de `1_scripts/7_analise_assintotica.py` e de `7_resultados/analise_assintotica.json` |
| Etapa 6 — gráficos | Manutenção de `1_scripts/6_gerar_graficos.py` (PNGs e CSVs de resultados) |
| Etapa 5 — experimentos | Reescrita da medição de `1_scripts/5_experimentar.py` (correção da inversão de *ranking* por *timing* de subprocesso) |
| Etapa 8 — robustez | `1_scripts/8_avaliar_robustez.py` e os três artefatos em `7_resultados/` |
| Aplicação web | 27 commits em `src/`, `index.html`, `package.json`, `public/data/` |
| Infraestrutura | `.github/` (workflows), `vercel.json`, `metadata.json`, `.gitignore`, `.vscode/settings.json` |
| Documentação | Revisões em `README.md`, além de `ANALISE_CORRETUDE_COMPLEXIDADE.md`, `RAG_GENAI.md`, `DECLARACAO_IA.md` e `LICENSE` |

---

## Contribuição por etapa do *pipeline*

| Etapa | Produto principal | Responsável principal |
|---|---|---|
| 1 — Pré-processamento | `3_dados/documentos_normalizados.json` | Diego Bispo / Laryssa Andrade |
| 2 — Fragmentação (*chunking*) | `4_chunks/chunks.json` (182 chunks) | Kaio Santos |
| 3 — Índice invertido | `5_indexacao/indice_invertido.json` (4 061 termos) | Diego Bispo |
| 4 — Busca e ordenação | `6_busca_lexical/*` (BM25 + Merge Sort + Top-k) | Gabriel Marques / Kaio Santos |
| 5 — Bateria de experimentos | `7_resultados/relatorio_experimentos.json` | Victor Melo |
| 6 — Tabelas e gráficos | `7_resultados/*.png`, `7_resultados/*.csv` | Victor Melo |
| 7 — Análise assintótica | `7_resultados/analise_assintotica.json` | Victor Melo |
| 8 — Robustez e *baseline* | `7_resultados/avaliacao_robustez.json`, `tabela_robustez.csv`, `tabela_baseline_ordenacao.csv` | Victor Melo |
| Aplicação web (demonstração) | `src/` (React + Vite) | Laryssa Andrade / Victor Melo |
| Análise de corretude e complexidade | `ANALISE_CORRETUDE_COMPLEXIDADE.md` | Equipe (revisão de Victor Melo) |
| Relação com RAG/IA generativa | `RAG_GENAI.md` | Equipe |
| Declaração de uso de IA | `DECLARACAO_IA.md` | Equipe |

---

## Entregáveis não rastreados por Git

Os itens abaixo são exigidos pelo enunciado (Seções 10 e 11) e **não podem ser
apurados automaticamente**, porque são produzidos fora do repositório. Cada
integrante deve confirmar sua participação antes da entrega:

| Entregável | Exigido por | Responsável / participação |
|---|---|---|
| Relatório técnico em PDF | Seção 10, item 1 | *(a preencher pela equipe)* |
| Apresentação de slides | Seção 12 | *(a preencher pela equipe)* |
| Vídeo de até 10 min (participação de **todos** os integrantes) | Seção 11 | Diego Bispo, Gabriel Marques, Laryssa Andrade, Kaio Santos, Victor Melo |
| Revisão final e submissão no Google Classroom | Seções 11 e 10 | *(a preencher pela equipe)* |

---

## Declaração

Os integrantes abaixo declaram que as contribuições descritas neste documento
refletem a participação efetiva de cada um na atividade:

| Integrante | Assinatura |
|---|---|
| Diego Bispo | |
| Gabriel Marques | |
| Laryssa Andrade | |
| Kaio Santos | |
| Victor Melo | |
