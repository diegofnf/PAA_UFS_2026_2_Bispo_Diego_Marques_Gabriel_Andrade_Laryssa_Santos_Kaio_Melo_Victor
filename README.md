[![Open in Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

# Regulamentos acadêmicos e manuais públicos

Corretude, eficiência e recuperação de contexto para IA generativa.

Este README é o manual operacional do repositório. O relatório técnico concentra a fundamentação, as provas, a análise detalhada, os experimentos e a discussão; esta página será atualizada à medida que esses artefatos forem produzidos.

## Relatório técnico

- [Relatório](https://docs.google.com/document/d/1RLEssVnXO0mOw0kx70mevGKRufop8sq1oqN-WQzNv2I/edit?usp=sharing)
  
## Vídeo da atividade

- [Vídeo](https://youtu.be/6Qv1OSFnZBo)

## Apresentação

- [Apresentação](https://drive.google.com/file/d/1lAGornS6dA-uNCQJ60wJdmWgpHZDu0LI/view?usp=sharing)

As apresentações estão em desenvolvimento e serão atualizadas com os resultados finais.

## Orquestrador no Google Colab

- [Abrir `orquestrador_pipeline.ipynb` no Google Colab](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)


## Estrutura do repositório

- `orquestrador_pipeline.ipynb`: execução integrada no Google Colab.
- `1_scripts/1_processar_documentos.py`: inventário, extração, normalização e validação.
- `2_corpus/`: PDFs utilizados no corpus.
- `3_dados/`: JSONs gerados pelo pipeline com extração PyMuPDF e normalização.
- `4_chunks/`: segmentação de texto com janelamento deslizante e sobreposição; chunks prontos para indexação (`chunks.json`) e relatório estatístico da etapa (`relatorio_chunking.json`).
- `5_indexacao/`: índice invertido (`indice_invertido.json`) e relatório da indexação (`relatorio_indexacao.json`).
- `6_busca_lexical/`: candidatos com scores gerados (`candidatos_busca.json` na busca indexada e `candidatos_linear.json` na busca linear), métricas das duas buscas (`relatorio_busca.json` e `relatorio_busca_linear.json`), candidatos ordenados pelo Merge Sort (`candidatos_ordenados.json`), Top-k (`candidatos_topk.json`) e contadores da ordenação (`relatorio_ordenacao.json`).
- `7_resultados/`: relatório consolidado das baterias experimentais (`relatorio_experimentos.json`), tabela consolidada (`tabela_resultados.csv`), análise assintótica do pipeline (`analise_assintotica.json` e `tabela_analise_assintotica.csv`), avaliação de robustez e *baseline* de ordenação (`avaliacao_robustez.json`, `tabela_robustez.csv` e `tabela_baseline_ordenacao.csv`) e os gráficos dos resultados (`grafico_tempo_execucao.png`, `grafico_busca_comparativo.png`, `grafico_escalabilidade_merge_sort.png`, `grafico_zipf.png`, `grafico_memoria_configuracoes.png`, `grafico_etapas_pipeline.png` e `grafico_analise_assintotica.png`).
- `src/`: aplicação web em React + Vite que consulta os artefatos já versionados em `public/data/`. O motor de busca em `src/utils/searchEngine.ts` reimplementa o Okapi BM25 da Etapa 4 com paridade numérica (ver [Paridade da busca com a Etapa 4](#paridade-da-busca-com-a-etapa-4)).
- `ANALISE_CORRETUDE_COMPLEXIDADE.md`: justificativa de corretude, análise no modelo RAM, melhor/pior/caso médio, recorrências e complexidade de espaço.
- `RAG_GENAI.md`: relação do contexto recuperado com aplicações RAG e IA generativa.
- `DECLARACAO_IA.md`: declaração de uso crítico de IA generativa.
- `CONTRIBUICOES.md`: contribuição individual dos integrantes.
- `VIDEO.md`: dados e roteiro do vídeo da atividade.
- `LICENSE`: licença do código e condições de uso do corpus.


## Dependências

Python 3, `PyMuPDF`, `nltk` e `matplotlib`. Os testes da Etapa 4 requerem `pytest`.

## Ambiente

Execução validada em Windows com Python 3. O script usa caminhos relativos ao repositório.

## Instalação

```bash
python -m pip install PyMuPDF nltk matplotlib pytest
python -c "import nltk; nltk.download('stopwords')"
```

## Reprodução

1. Obter ou utilizar os PDFs do diretório `2_corpus/`.
2. Preparar o ambiente conforme as seções acima.
3. Executar os comandos do pipeline (etapas 1 a 4), depois os experimentos (etapa 5), a análise assintótica (etapa 7), a avaliação de robustez (etapa 8) e, por fim, a consolidação (etapa 6).
4. Conferir os resultados, tabelas, gráficos e dados brutos gerados.

Todas as medições de tempo devem ser feitas no **mesmo ambiente**. Os valores registrados em `relatorio_experimentos.json` e nos gráficos foram obtidos em Windows 11 (AMD64) com Python 3.14.7; misturar máquinas ou versões invalida a comparação entre configurações.

## Testes

```bash
python -m pytest 1_scripts/test_etapa_4.py
```

A suíte cobre a corretude da ordenação, o critério de desempate
`(−score, id_chunk)`, a contagem de comparações, a seleção do Top-k e os casos
de borda (lista vazia, `k` igual a 1, `k` maior que o número de candidatos e
empates totais). Resultado esperado: **14 testes aprovados**.

Os "resultados esperados" dos experimentos estão nos artefatos versionados em
`7_resultados/`, e a verificação de que eles não são apenas plausíveis mas
**reproduzíveis** é feita por conferência aritmética entre contadores: a soma
`comparacoes_score + comparacoes_id_chunk` deve igualar `comparacoes_totais`
(351 + 18 = 369), o número de chamadas recursivas deve ser `2n − 1` (149 para
n = 75) e a profundidade máxima deve ser `1 + ⌈log₂ n⌉` (8 para n = 75).

## Corpus

Corpus normativo e orientativo público do PROCC/UFS e normas correlatas. Uso exclusivamente acadêmico.

- **Acesso/download:** 02/09/2026, às 21h10.
- **Quantidade:** 7 documentos, 83 páginas e aproximadamente 4,50 MB.
- **Idioma/formato:** português brasileiro; arquivos PDF.
- **Licença e condições de uso:** os PDFs são **documentos institucionais públicos**, publicados pelo próprio PROCC/UFS em seus canais oficiais (SIGAA) e pelo Edital CAPES, e são utilizados aqui **exclusivamente para fins acadêmicos e não comerciais**, sem redistribuição com finalidade comercial. Eles **não** estão cobertos pela licença MIT que se aplica ao código da equipe: a licença do repositório cobre apenas os scripts e artefatos produzidos pelo grupo, e cada documento permanece sujeito às condições do órgão emissor. As URLs oficiais de origem constam da tabela abaixo, o que permite verificar a procedência de cada arquivo. Ver [`LICENSE`](LICENSE).
- **Dados removidos ou anonimizados:** nenhum — o corpus é composto por atos normativos públicos, sem dados pessoais.
- **Limpeza e normalização:** Unicode NFC, quebras de linha, espaços repetidos e hifenização entre linhas; texto original preservado.


| Documento | URL oficial |
|---|---|
| IN 02/2026/PROCC — Destinação de recursos financeiros | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=5040212&key=bd7f4126e48c0ff0c3f3ecd020bea2af) |
| IN 01/2026/PROCC — Credenciamento, recredenciamento e distribuição de vagas de orientação docente | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=5025297&key=2d84693e082547f2c3b9e5a7211baf63) |
| Edital CAPES nº 14/2023 — PRAPG | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4214078&key=9a30771aef926507ec26e66ff5da6260) |
| IN 01/2023/PROCC — Estrutura curricular do Mestrado | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4024039&key=3935a3b7b0d57462398d13c8fa68def5) |
| IN 01/2024/PROCC — Critérios para atribuição de bolsas | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4357246&key=807372ebd6adf4d3ad63cd51277fec38) |
| Resolução nº 04/2021/CONEPE — Normas Acadêmicas da Pós-Graduação | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=2737960&key=1861aeae080b4f6318206935e3b17414) |
| Resolução nº 29/2022/CONEPE — Regimento Interno do PROCC | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4218408&key=0f7e24ac2195143e5735697d19cb43ac) |


## Aplicação Web — Recuperação Lexical e Ordenação (PROCC/UFS)

Interface web interativa desenvolvida para busca, recuperação e ordenação de contexto sobre os regulamentos acadêmicos do Programa de Pós-Graduação em Ciência da Computação (PROCC/UFS).

🔗 **[Acessar a Aplicação Web](https://procc-recuperacao-documentos.vercel.app/)**

> A publicação é feita na **Vercel** pelo workflow [`.github/workflows/deploy-vercel.yml`](.github/workflows/deploy-vercel.yml) a cada push em `main`.
> O **GitHub Pages não é utilizado**: o `index.html` da raiz é o arquivo de desenvolvimento do Vite e, quando servido estaticamente (por exemplo, pelos forks), aponta para `/src/main.tsx` e resulta em página em branco.

### Paridade da busca com a Etapa 4

A aba **Busca Lexical & Top-K** reimplementa em TypeScript o mesmo motor de
`1_scripts/4_buscar_e_ordenar.py`, de modo que os números exibidos no navegador
coincidam com os artefatos versionados — não se trata de uma demonstração
simplificada:

| Regra | Implementação |
|---|---|
| Tokenização | Unicode NFC + *casefold*, `\p{L}\p{N}` (equivalente ao `\w` Unicode do Python) |
| Stopwords | Lista do **NLTK** em português (207 palavras), em [`src/utils/stopwords.ts`](src/utils/stopwords.ts) |
| `\|D\|` e `avgdl` | Medidos em **tokens do texto** do *chunk*, como no script Python |
| IDF | `ln(1 + (N − DF + 0,5) / (DF + 0,5))` |
| TF | `(freq × (k1 + 1)) / (freq + k1 × (1 − b + b × \|D\| / avgdl))`, com `k1 = 1,5` e `b = 0,75` |
| Ordenação | Merge Sort com critério `(−score, id_chunk)` |

Com a consulta canônica do trabalho (`"critérios para atribuição de bolsas e
requisitos de matrícula"`), a aplicação devolve **exatamente** o mesmo resultado
de `6_busca_lexical/candidatos_topk.json`:

| Métrica | Valor na aplicação e no artefato |
|---|---|
| Tokens da consulta | 9 |
| Stopwords removidas | 4 (`para`, `de`, `e`, `de`) |
| Termos distintos | 5 |
| Candidatos | 75 |
| Comparações do Merge Sort | 369 |
| Top-1 | `chunk_0131` — score 9,6206 |

> **Nota de portabilidade.** Em JavaScript `\w` é *ASCII-only* por especificação,
> mesmo com a flag `u`: `/[^\W_]+/u` separa `"critérios"` em `crit` + `rios`. O
> tokenizador usa `\p{L}\p{N}` com a flag `u` para reproduzir o comportamento
> Unicode de `\w` do Python. Sem esse ajuste, a busca indexada deixava de
> encontrar termos acentuados e a contagem de candidatos divergia do relatório.

## Licença

O **código-fonte** deste repositório (scripts em `1_scripts/`, aplicação web em
`src/`, *notebook* e documentação produzida pela equipe) está licenciado sob a
**Licença MIT** — ver [`LICENSE`](LICENSE).

Os **PDFs do corpus** em `2_corpus/` **não** estão cobertos por essa licença:
são documentos institucionais públicos, publicados pelos próprios órgãos
emissores, e são utilizados neste trabalho exclusivamente para fins acadêmicos e
não comerciais. As URLs oficiais de origem estão na seção [Corpus](#corpus), o
que permite verificar a procedência de cada arquivo.

Este repositório não contém chaves, senhas, tokens ou dados pessoais. Arquivos
grandes (PDFs do corpus e `node_modules/`) são controlados por `.gitignore`, e as
instruções para obtê-los ou reproduzi-los estão nas seções
[Instalação](#instalação), [Execução](#execução) e [Reprodução](#reprodução).


