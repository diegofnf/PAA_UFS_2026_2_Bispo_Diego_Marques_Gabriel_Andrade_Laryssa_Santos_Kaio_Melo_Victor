# Vídeo da atividade

Arquivo exigido pela **Seção 11** do enunciado: *"no arquivo `VIDEO.md` ou
`video.txt` do repositório, contendo URL, data de gravação e identificação dos
participantes"*.

> ⚠️ **PENDÊNCIA — preencher antes da entrega (23/09/2026, 23h59).**
> O vídeo ainda não foi gravado. Os campos marcados com `⬜` precisam ser
> substituídos pelas informações reais. A URL deve permanecer acessível
> **sem solicitação de acesso ao docente** até o encerramento da avaliação.

---

## Dados do vídeo

| Campo | Valor |
|---|---|
| **URL** | ⬜ *(inserir link público — YouTube não listado, Google Drive com acesso por link, ou equivalente)* |
| **Data de gravação** | ⬜ `____/____/2026` |
| **Duração** | ⬜ `____ min ____ s` — **limite máximo: 10 minutos** |
| **Plataforma de hospedagem** | ⬜ *(YouTube / Google Drive / outra)* |
| **Verificação de acesso** | ⬜ *(conferir em janela anônima que o vídeo abre sem pedir permissão)* |

A URL acima também deve constar em **outros três lugares**, conforme a Seção 11:

1. `README.md` do repositório, em seção intitulada **"Vídeo da atividade"** ✅ *(seção já criada; falta apenas o link)*
2. Relatório técnico em PDF, na capa ou seção inicial ⬜
3. Área da atividade no Google Classroom, exclusivamente como link ⬜

---

## Identificação dos participantes

**Equipe:** `PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Farias_Melo_Victor`
**Tema/corpus:** 7 documentos normativos do PROCC/UFS e normas correlatas (83 páginas, 182 chunks) — recuperação lexical de contexto com Okapi BM25, Merge Sort e seleção Top-k.

Todos os 5 integrantes participam do vídeo, com identificação clara da
contribuição de cada um:

| Integrante | Trecho sob sua responsabilidade no vídeo |
|---|---|
| **Diego Bispo** | Corpus: fonte, licença, data de acesso e características; definição formal do problema |
| **Gabriel Marques** | Etapa 4 — busca lexical: BM25, critério de desempate `(−score, id_chunk)` e Top-k |
| **Laryssa Santos** | Etapas 1–6 — extração, normalização, *chunking*, índice invertido e demonstração do protótipo |
| **Kaio Farias** | Casos de teste, resultados esperados e evidência de corretude pela suíte automatizada |
| **Victor Melo** | Análise RAM, recorrrências, análise assintótica (Etapa 7), resultados experimentais e relação com RAG/IA generativa |

---

## Roteiro sugerido (≤ 10 min)

A Seção 11 lista 10 tópicos obrigatórios. Sugestão de distribuição para caber em
10 minutos, reservando ~1 min de demonstração do protótipo:

| # | Tópico exigido pela Seção 11 | Tempo | Responsável |
|---|---|---|---|
| 1 | Identificação da equipe, tema e corpus | 0:30 | Diego Bispo |
| 2 | Problema de recuperação de contexto | 1:00 | Diego Bispo |
| 3 | Algoritmos implementados (busca linear, Merge Sort, busca indexada) | 2:00 | Gabriel Marques + Laryssa Santos |
| 4 | **Demonstração breve do protótipo** | 1:00 | Laryssa Santos |
| 5 | Justificativa de corretude (invariantes de laço e indução) | 1:30 | Kaio Farias |
| 6 | Análise assintótica e recorrências | 1:30 | Victor Melo |
| 7 | Resultados experimentais e gráfico principal | 1:00 | Victor Melo |
| 8 | Relação com RAG ou IA generativa | 1:00 | Victor Melo |
| 9 | Limitações, *trade-offs* e decisões de projeto | 0:30 | Diego Bispo |
| — | **Total** | **10:00** | |

### Materiais de apoio para a gravação

- **Gráfico principal:** `7_resultados/grafico_escalabilidade_merge_sort.png`
  (escalabilidade do Merge Sort) e `7_resultados/grafico_busca_comparativo.png`
  (comparação entre as configurações de busca)
- **Evidência de corretude:** terminar a demonstração executando
  `python -m pytest 1_scripts/test_etapa_4.py` e mostrando **14 passed**
- **Comparativo com biblioteca de referência (Seção 5.2, item 5):**
  `7_resultados/tabela_baseline_ordenacao.csv` — evidencia que o `merge_sort`
  da equipe produz ordem e Top-5 idênticos a `sorted()` (Timsort) e a
  `heapq.nsmallest` sobre os mesmos 75 candidatos reais
- **Bateria de robustez (Seção 7.3):** `7_resultados/tabela_robustez.csv` —
  18 execuções, 0 falhas
- **Demonstração do protótipo:** aplicação React/Vite (`npm ci && npm run dev`)
  consultando o índice já versionado em `public/data/`

### Lembretes

- O vídeo **complementa, mas não substitui** a apresentação oral de 24/09/2026
  (Seção 12).
- O vídeo **não** deve ser anexado ao Google Classroom: apenas a URL, como link.
- Conferir a duração antes de publicar: o limite de 10 minutos é explícito.
