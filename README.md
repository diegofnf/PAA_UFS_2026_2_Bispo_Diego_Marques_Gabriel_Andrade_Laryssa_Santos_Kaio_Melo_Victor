[![Abrir no Colab](https://img.shields.io/badge/Abrir%20no-Colab-F9AB00?logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/av2/av2/orquestrador_av2.ipynb)

# PAA — Atividade 2 — Seleção de contexto com orçamento de tokens

Grupo 2 · PROCC/UFS · Projeto e Análise de Algoritmos · 2026.2

**Trilha A:** mochila 0/1 por programação dinâmica, comparada com seleção gulosa por relevância/custo. A AV2 evolui o protótipo de recuperação do mesmo corpus para escolher evidências que caibam em um orçamento de tokens.

**Situação em 15/10/2026:** etapa 1 concluída e publicada. Os seletores, a comparação experimental e a integração com LLM estão planejados; ainda não há resultados de PD versus guloso.

## Relatório técnico

- [Relatório da AV2 — Google Docs](https://docs.google.com/document/d/1cFoJsM_uP5D8M5gXjQQlGoIUPa56ldwupIIRD0V7Y_8/edit)
- [Texto de continuidade e preparação](av2/CONTINUIDADE_AV1.md)

## Vídeo da atividade

Vídeo da **AV2** a produzir, com participação de todos e duração de até 10 minutos. O link será incluído aqui e no relatório quando publicado.

## Apresentação

- [Apresentação da AV2 — Google Slides](https://docs.google.com/presentation/d/1FjPmWpVQE1aJELaLnQo0peaQ_8FZfcmRb1jCor3uHu0/edit)

## Orquestrador no Google Colab

- [Abrir o notebook exclusivo da AV2](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/av2/av2/orquestrador_av2.ipynb)

No Colab, execute todas as células. O notebook clona a branch `av2`, instala as dependências, prepara as instâncias e executa os testes. Não requer chave de API nem chama uma LLM.

## Estrutura do repositório

| Caminho | Papel na AV2 |
|---|---|
| `av2/preparar_instancias.py` | Validação, associação dos scores e contagem de tokens. |
| `av2/dados/` | Corpus tokenizado, instâncias e relatório de preparação. |
| `av2/orquestrador_av2.ipynb` | Execução independente da etapa 1. |
| `av2/test_preparar_instancias.py` | Testes da preparação. |
| `av2/evidencias/` | Notebook executado, matriz de testes, versões e resultados. |
| `av2/README.md` | Contrato dos dados e detalhes técnicos. |
| `av2/REGISTRO_ETAPA_1.md` | Contribuição e uso crítico de IA nesta entrega. |
| `2_corpus/`, `3_dados/`, `4_chunks/`, `5_indexacao/`, `6_busca_lexical/` | Base de recuperação reutilizada pela AV2. |
| `.github/workflows/av2-etapa1.yml` | Validação automática em Linux. |

Uma branch representa o estado completo do projeto. Os arquivos herdados permanecem porque a AV2 depende do corpus e da recuperação existentes. O código novo e seus resultados ficam em `av2/`.

## Dependências e ambiente

Python 3.12 validado em Windows e Linux. A preparação utiliza **tiktoken 0.14.0**; as dependências de testes e notebook estão fixadas em `av2/requirements-validacao.txt`.

## Instalação

Na raiz de uma cópia da branch `av2`:

```bash
python -m pip install -r av2/requirements-validacao.txt
```

## Reprodução

```bash
python av2/preparar_instancias.py
```

O comando apenas lê os chunks e candidatos completos já versionados. Associa `w_i` (tokens) e `v_i` (score BM25), preserva texto e origem e gera capacidades **512, 1024, 2048 e 4096**.

| Saída | Conteúdo |
|---|---|
| [chunks_tokenizados.json](av2/dados/chunks_tokenizados.json) | Os 182 chunks, com custo e benefício associados. |
| [instancias.json](av2/dados/instancias.json) | Os 75 candidatos positivos e quatro cenários de capacidade. |
| [relatorio_preparacao.json](av2/dados/relatorio_preparacao.json) | Tempos separados, consulta, tokenizer, hashes e commit de execução. |

Para as próximas etapas, carregue `itens` por `id_chunk` e utilize `W` e `ids_itens` de cada cenário. Ambos os seletores devem receber a mesma entrada. Consulte o [contrato completo](av2/README.md#contrato-dos-arquivos-de-saída).

## Tokenizer e orçamento

- Biblioteca/versão: `tiktoken==0.14.0`.
- Encoding: `cl100k_base`; método: `encode_ordinary`.
- Custo: contagem exata do texto original para esse encoding, sem estimativa por palavras.
- `W`: orçamento da soma dos custos individuais dos chunks. Instruções, consulta, citações e resposta exigem espaço adicional.
- Modelo gerador ainda não definido. A integração deverá contar o prompt final com o tokenizer do modelo escolhido.

## Testes e evidências

```bash
python -m pytest av2/test_preparar_instancias.py 1_scripts/test_etapa_4.py -q
```

**48 testes aprovados:** 34 da preparação e 14 de regressão da recuperação reutilizada. Esse total é de testes, não de medições do futuro benchmark.

- [Matriz de resultados esperados e observados](av2/evidencias/README.md)
- [Notebook executado em cópia limpa](av2/evidencias/notebook_executado.ipynb)
- [Validação automática em Linux](https://github.com/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/actions/workflows/av2-etapa1.yml)

## Corpus

A AV2 mantém os **7 documentos normativos e orientativos públicos do PROCC/UFS, CAPES e CONEPE**, com 83 páginas e 182 chunks. Fontes e identificação dos documentos estão no [catálogo](3_dados/catalogo_documentos.json). Não são adicionados documentos ao caso padrão.

O caso atual usa uma consulta sobre bolsas e matrícula. A comparação final deverá cobrir duas escalas de entrada e pelo menos três repetições por cenário; variar apenas `W` não cumpre esse requisito.

## Etapas e responsáveis

| Etapa | Responsável | Situação |
|---|---|---|
| 1 — Ingestão e tokenização | Diego Bispo | Concluída |
| 2 — Especificação e baseline gulosa | Kaio Santos | Planejada |
| 3 — Programação dinâmica | Diego Bispo e Kaio Santos | Planejada |
| 4 — Corretude e limites | Gabriel Marques | Planejada |
| 5 — Complexidade e integração com IA | Victor Melo | Planejada |
| 6 — Métricas e benchmark | Laryssa Andrade | Planejada |

## Versionamento e prazos

O desenvolvimento acontece na branch **`av2`**. A versão da primeira atividade permanece preservada na `main` e na tag `av1-entrega`. A tag `av2-entrega` será criada somente ao concluir a atividade inteira.

Os dados da etapa 1 registram o commit de código `b984f37`; o commit `c4d7007` guarda as instâncias e evidências dessa execução limpa.

- Entrega da AV2: **04/11/2026, às 23h59**.
- Apresentação: **05/11/2026**.

## Licença

O código produzido pela equipe é distribuído sob a [licença MIT](LICENSE). Os PDFs institucionais mantêm as condições de seus órgãos emissores e não são abrangidos pela licença do código.

