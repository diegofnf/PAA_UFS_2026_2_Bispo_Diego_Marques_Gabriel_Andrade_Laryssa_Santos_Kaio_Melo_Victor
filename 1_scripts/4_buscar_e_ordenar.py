"""Etapa 4 — Busca Lexical, Score (BM25 / Simples) e Estrutura para Merge Sort e Top-k.

Este script implementa:
1. Busca lexical e geração de candidatos:
   - Tokenização padronizada da consulta (idêntica ao índice invertido: Unicode NFC + casefold);
   - Remoção de stopwords em língua portuguesa via biblioteca NLTK;
   - Cálculo modular de métricas de relevância:
     a) Okapi BM25 (padrão): TF com saturação assintótica, IDF de Robertson-Spärck Jones
        e normalização pelo comprimento médio dos chunks (avgdl);
     b) Pontuação Simples: soma das frequências brutas dos termos filtrados;
   - Seleção dinâmica da métrica via linha de comando (--metrica) ou chamada funcional;
   - Busca linear sobre todos os N chunks com contagem exata de comparações;
   - Busca indexada sobre o índice invertido (recuperação otimizada por postings lists);
   - Tratamento formal de casos de borda (consultas vazias, termos inexistentes, apenas stopwords);
   - Geração de artefatos JSON ('candidatos_linear.json' e 'candidatos_indexada.json').

2. Algoritmo de ordenação e seleção Top-k (pontos de extensão para continuidade):
   - Leitura dos arquivos de candidatos;
   - Procedimento de ordenação Merge Sort manual (recorrência T(N) = 2T(N/2) + Θ(N));
   - Desempate determinístico (maior score decrescente, menor id_chunk crescente);
   - Seleção dos Top-k e geração de resultados finais.
"""

from __future__ import annotations
import argparse
import json
import math
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
import tracemalloc

import nltk
from nltk.corpus import stopwords

# Padrão idêntico ao do script 1_scripts/3_construir_indice_invertido.py
PADRAO_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


# ==============================================================================
# 1. TOKENIZAÇÃO, STOPWORDS E NORMALIZAÇÃO
# ==============================================================================

def carregar_stopwords_nltk() -> set[str]:
    """Carrega e normaliza as stopwords em português da biblioteca NLTK."""
    try:
        palavras = stopwords.words("portuguese")
    except LookupError:
        nltk.download("stopwords", quiet=True)
        palavras = stopwords.words("portuguese")
    return {unicodedata.normalize("NFC", p).casefold() for p in palavras}


def tokenizar(texto: str) -> list[str]:
    """Gera tokens alfanuméricos com acentos preservados e minúsculas (Unicode NFC + casefold)."""
    if not texto:
        return []
    texto_normalizado = unicodedata.normalize("NFC", str(texto)).casefold()
    return PADRAO_TOKEN.findall(texto_normalizado)


def processar_consulta(consulta: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Processa a consulta textual: tokeniza, remove stopwords via NLTK e deduplica os termos.
    
    Retorna:
        - tokens_consulta: todos os tokens extraídos da consulta original;
        - stopwords_removidas: tokens classificados como stopwords e filtrados;
        - termos_apos_filtro_stopwords: tokens preservados após a remoção de stopwords;
        - termos_distintos_consulta: termos únicos utilizados para cálculo do score.
    """
    tokens_consulta = tokenizar(consulta)
    sw = carregar_stopwords_nltk()

    stopwords_removidas = []
    termos_apos_filtro = []

    for token in tokens_consulta:
        if token in sw:
            stopwords_removidas.append(token)
        else:
            termos_apos_filtro.append(token)

    termos_distintos = []
    vistos = set()
    for token in termos_apos_filtro:
        if token not in vistos:
            vistos.add(token)
            termos_distintos.append(token)

    return tokens_consulta, stopwords_removidas, termos_apos_filtro, termos_distintos


# ==============================================================================
# 2. MÉTRICAS DE RELEVÂNCIA: PONTUAÇÃO SIMPLES E OKAPI BM25
# ==============================================================================

def calcular_estatisticas_corpus(chunks: list[dict] | dict[str, dict]) -> tuple[int, float, dict[str, int]]:
    """Extrai estatísticas globais do corpus necessárias para cálculo do Okapi BM25.
    
    Retorna:
        - N: total de documentos (chunks) no corpus;
        - avgdl: comprimento médio em número de tokens (média de |D|);
        - comprimentos_doc: dicionário mapeando id_chunk -> comprimento em tokens (|D|).
    """
    lista_chunks = chunks if isinstance(chunks, list) else list(chunks.values())
    N = len(lista_chunks)
    comprimentos_doc = {}
    total_tokens = 0

    for c in lista_chunks:
        cid = c.get("id_chunk", "")
        texto = c.get("texto", "")
        tokens = tokenizar(texto)
        tamanho = len(tokens)
        comprimentos_doc[cid] = tamanho
        total_tokens += tamanho

    avgdl = (total_tokens / N) if N > 0 else 0.0
    return N, avgdl, comprimentos_doc


def calcular_idf_bm25(total_documentos: int, doc_freq: int) -> float:
    """Calcula o Inverse Document Frequency (IDF) com suavização probabilística Robertson-Spärck Jones.
    
    Fórmula:
        IDF(t) = ln(1 + (N - DF(t) + 0.5) / (DF(t) + 0.5))
    
    Propriedades Teóricas:
        - Termos raros no corpus (DF baixo) recebem IDF alto (alto poder discriminador);
        - Termos frequentes no corpus (DF alto) recebem IDF baixo;
        - A adição de +1 dentro do logaritmo (suavização de Lucene/BM25 standard)
          garante que o IDF permaneça sempre não negativo (>= 0), evitando scores negativos.
    
    Complexidade Temporal: O(1).
    """
    if total_documentos <= 0 or doc_freq <= 0:
        return 0.0
    return math.log(1.0 + (total_documentos - doc_freq + 0.5) / (doc_freq + 0.5))


def calcular_tf_bm25(
    freq: int,
    doc_len: int,
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Calcula o componente TF com saturação e normalização de comprimento do Okapi BM25.
    
    Fórmula:
        TF_BM25(t, D) = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (|D| / avgdl)))
    
    Justificativa das Constantes e Comportamento:
        - k1 (padrão 1.5): Controla a saturação da frequência do termo.
          À medida que freq -> infinito, TF_BM25 assintotiza em (k1 + 1), impedindo
          que repetições exaustivas de um mesmo termo superem a presença de outros termos da consulta.
        - b (padrão 0.75): Controla a penalização pelo comprimento do documento (|D| / avgdl).
          Documentos muito extensos que contêm o termo por mero acaso são penalizados,
          enquanto documentos curtos e densos são valorizados.
    
    Complexidade Temporal: O(1).
    """
    if freq <= 0:
        return 0.0
    ajuste_tamanho = 1.0 - b + (b * (doc_len / avgdl) if avgdl > 0 else 0.0)
    denominador = freq + k1 * ajuste_tamanho
    if denominador <= 0:
        return 0.0
    return (freq * (k1 + 1.0)) / denominador


def calcular_score_simples(frequencias_termos: dict[str, int]) -> int:
    """Calcula a pontuação linear simples: soma das frequências brutas dos termos filtrados.
    
    Fórmula:
        score_simples(D, q) = sum_{t in q} freq(t, D)
    
    Complexidade Temporal: O(m), onde m é o número de termos distintos da consulta.
    """
    return sum(frequencias_termos.values())


def calcular_score_bm25(
    frequencias_termos: dict[str, int],
    doc_len: int,
    avgdl: float,
    idfs: dict[str, float],
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Calcula a pontuação Okapi BM25 acumulando o produto TF_BM25 * IDF de cada termo consultado.
    
    Fórmula:
        score_bm25(D, q) = sum_{t in q} IDF(t) * TF_BM25(t, D)
    
    Complexidade Temporal: O(m), onde m é o número de termos distintos da consulta.
    """
    score = 0.0
    for termo, freq in frequencias_termos.items():
        idf = idfs.get(termo, 0.0)
        tf = calcular_tf_bm25(freq, doc_len, avgdl, k1, b)
        score += idf * tf
    return score


# ==============================================================================
# 3. MECANISMO DE BUSCA LINEAR
# ==============================================================================

def buscar_linear(
    chunks: list[dict],
    consulta: str,
    metrica: str = "bm25",
    k1: float = 1.5,
    b: float = 0.75,
    estatisticas_corpus: tuple[int, float, dict[str, int]] | None = None,
) -> tuple[list[dict], dict]:
    """Executa a busca linear varrendo todos os N chunks do corpus.
    
    Suporta as métricas de relevância:
        - 'bm25' (Okapi BM25 com saturação, IDF e normalização avgdl);
        - 'simples' (contagem linear de frequências).
    
    Complexidade Assintótica:
        N = total de chunks no corpus (182)
        m = total de termos distintos da consulta após filtro de stopwords
        L = tamanho médio do chunk em tokens (~204,77)
        Custo Temporal: O(N * (L + m))
        Custo Espacial: O(N) para armazenamento dos candidatos
    
    Retorna:
        - candidatos: lista de chunks cujo score > 0 (não ordenados);
        - metricas: dicionário com metadados e estatísticas da varredura linear.
    """
    inicio = time.perf_counter()
    tokens_consulta, stopwords_removidas, termos_apos_filtro, termos_distintos = processar_consulta(consulta)

    # Obtenção ou reutilização das estatísticas globais do corpus
    if estatisticas_corpus is not None:
        N, avgdl, doc_lengths = estatisticas_corpus
    else:
        N, avgdl, doc_lengths = calcular_estatisticas_corpus(chunks)

    # Caso de borda: consulta vazia ou sem termos válidos após filtro de stopwords
    if not termos_distintos:
        tempo = round(time.perf_counter() - inicio, 6)
        metricas = {
            "configuracao": "linear",
            "metrica_score": metrica,
            "total_chunks_corpus": N,
            "chunks_examinados": N,
            "tokens_consulta": tokens_consulta,
            "stopwords_removidas": stopwords_removidas,
            "termos_apos_filtro_stopwords": termos_apos_filtro,
            "termos_distintos_consulta": termos_distintos,
            "total_candidatos": 0,
            "total_comparacoes_termos": 0,
            "total_tokens_examinados": 0,
            "tempo_busca_segundos": tempo,
            "aviso": "Consulta vazia ou composta exclusivamente por stopwords / caracteres não alfanuméricos.",
        }
        return [], metricas

    total_comparacoes = 0
    total_tokens_examinados = 0
    chunks_com_matches = {}

    for chunk in chunks:
        cid = chunk["id_chunk"]
        texto_chunk = chunk.get("texto", "")
        tokens_chunk = tokenizar(texto_chunk)
        total_tokens_examinados += len(tokens_chunk)
        doc_len = doc_lengths.get(cid, len(tokens_chunk))

        contagens = Counter(tokens_chunk)
        total_comparacoes += len(termos_distintos)

        freqs = {}
        for termo in termos_distintos:
            f = contagens.get(termo, 0)
            if f > 0:
                freqs[termo] = f

        if freqs:
            chunks_com_matches[cid] = (chunk, freqs, doc_len)

    # Cálculo da frequência no documento (DF) para os termos da consulta
    df_map = {
        termo: sum(1 for _, freqs, _ in chunks_com_matches.values() if termo in freqs)
        for termo in termos_distintos
    }

    # Pré-cálculo de IDF se BM25 for a métrica selecionada
    idf_map = {}
    if metrica == "bm25":
        idf_map = {termo: calcular_idf_bm25(N, df_map[termo]) for termo in termos_distintos}

    candidatos = []
    for cid, (chunk, freqs, doc_len) in chunks_com_matches.items():
        if metrica == "bm25":
            score_calculado = calcular_score_bm25(freqs, doc_len, avgdl, idf_map, k1, b)
            score_final = round(score_calculado, 4)
        else:
            score_final = calcular_score_simples(freqs)

        if score_final > 0:
            candidatos.append({
                "id_chunk": chunk["id_chunk"],
                "id_documento": chunk.get("id_documento", ""),
                "nome_arquivo": chunk.get("nome_arquivo", ""),
                "paginas": chunk.get("paginas", []),
                "score": score_final,
                "frequencias_termos": freqs,
                "texto": chunk.get("texto", ""),
            })

    tempo = round(time.perf_counter() - inicio, 6)
    metricas = {
        "configuracao": "linear",
        "metrica_score": metrica,
        "parametros_metrica": {
            "metrica": metrica,
            **({"k1": k1, "b": b, "avgdl": round(avgdl, 4), "total_documentos_N": N} if metrica == "bm25" else {}),
        },
        "total_chunks_corpus": N,
        "chunks_examinados": N,
        "tokens_consulta": tokens_consulta,
        "stopwords_removidas": stopwords_removidas,
        "termos_apos_filtro_stopwords": termos_apos_filtro,
        "termos_distintos_consulta": termos_distintos,
        "document_frequencies": df_map,
        **({"inverse_document_frequencies": {t: round(v, 4) for t, v in idf_map.items()}} if metrica == "bm25" else {}),
        "total_candidatos": len(candidatos),
        "total_comparacoes_termos": total_comparacoes,
        "total_tokens_examinados": total_tokens_examinados,
        "tempo_busca_segundos": tempo,
    }
    return candidatos, metricas


# ==============================================================================
# 4. MECANISMO DE BUSCA INDEXADA
# ==============================================================================

def buscar_indexada(
    indice_invertido: dict,
    chunks_map: dict[str, dict],
    consulta: str,
    metrica: str = "bm25",
    k1: float = 1.5,
    b: float = 0.75,
    estatisticas_corpus: tuple[int, float, dict[str, int]] | None = None,
) -> tuple[list[dict], dict]:
    """Executa a busca utilizando o índice invertido da Etapa 3.
    
    Recupera diretamente as posting lists dos termos consultados.
    Obtém DF(t) em tempo O(1) a partir do tamanho da posting list e
    acumula as pontuações sem inspecionar documentos não relacionados.
    
    Complexidade Assintótica:
        m = total de termos distintos da consulta
        Custo Temporal: O(sum_{t in q} |Posting(t)|) << O(N * L)
        Custo Espacial: O(|Candidatos|)
    
    Retorna:
        - candidatos: lista de chunks cujo score > 0 (não ordenados);
        - metricas: dicionário com metadados e estatísticas da busca indexada.
    """
    inicio = time.perf_counter()
    tokens_consulta, stopwords_removidas, termos_apos_filtro, termos_distintos = processar_consulta(consulta)

    # Obtenção ou reutilização das estatísticas globais do corpus
    if estatisticas_corpus is not None:
        N, avgdl, doc_lengths = estatisticas_corpus
    else:
        N, avgdl, doc_lengths = calcular_estatisticas_corpus(chunks_map)

    if not termos_distintos:
        tempo = round(time.perf_counter() - inicio, 6)
        metricas = {
            "configuracao": "indexada",
            "metrica_score": metrica,
            "total_termos_vocabulario": len(indice_invertido),
            "tokens_consulta": tokens_consulta,
            "stopwords_removidas": stopwords_removidas,
            "termos_apos_filtro_stopwords": termos_apos_filtro,
            "termos_distintos_consulta": termos_distintos,
            "total_candidatos": 0,
            "total_postings_consultadas": 0,
            "tempo_busca_segundos": tempo,
            "aviso": "Consulta vazia ou composta exclusivamente por stopwords / caracteres não alfanuméricos.",
        }
        return [], metricas

    candidatos_map: dict[str, dict] = {}
    total_postings_consultadas = 0
    df_map = {}

    for termo in termos_distintos:
        entrada_termo = indice_invertido.get(termo)
        if not entrada_termo:
            df_map[termo] = 0
            continue

        postings = entrada_termo.get("chunks", [])
        total_postings_consultadas += len(postings)
        df_map[termo] = len(postings)

        for posting in postings:
            cid = posting["id_chunk"]
            freq = posting["frequencia"]

            if cid not in candidatos_map:
                chunk_info = chunks_map.get(cid, {})
                candidatos_map[cid] = {
                    "id_chunk": cid,
                    "id_documento": chunk_info.get("id_documento", ""),
                    "nome_arquivo": chunk_info.get("nome_arquivo", ""),
                    "paginas": chunk_info.get("paginas", []),
                    "score": 0,
                    "frequencias_termos": {},
                    "texto": chunk_info.get("texto", ""),
                }
            candidatos_map[cid]["frequencias_termos"][termo] = freq

    # Pré-cálculo de IDF se BM25 for a métrica selecionada
    idf_map = {}
    if metrica == "bm25":
        idf_map = {termo: calcular_idf_bm25(N, df_map[termo]) for termo in termos_distintos}

    # Atribuição da pontuação de acordo com a métrica selecionada
    for cid, cand in candidatos_map.items():
        doc_len = doc_lengths.get(cid)
        if doc_len is None:
            doc_len = len(tokenizar(cand.get("texto", "")))

        freqs = cand["frequencias_termos"]
        if metrica == "bm25":
            score_calculado = calcular_score_bm25(freqs, doc_len, avgdl, idf_map, k1, b)
            cand["score"] = round(score_calculado, 4)
        else:
            cand["score"] = calcular_score_simples(freqs)

    candidatos = [c for c in candidatos_map.values() if c["score"] > 0]
    tempo = round(time.perf_counter() - inicio, 6)

    metricas = {
        "configuracao": "indexada",
        "metrica_score": metrica,
        "parametros_metrica": {
            "metrica": metrica,
            **({"k1": k1, "b": b, "avgdl": round(avgdl, 4), "total_documentos_N": N} if metrica == "bm25" else {}),
        },
        "total_termos_vocabulario": len(indice_invertido),
        "tokens_consulta": tokens_consulta,
        "stopwords_removidas": stopwords_removidas,
        "termos_apos_filtro_stopwords": termos_apos_filtro,
        "termos_distintos_consulta": termos_distintos,
        "document_frequencies": df_map,
        **({"inverse_document_frequencies": {t: round(v, 4) for t, v in idf_map.items()}} if metrica == "bm25" else {}),
        "total_candidatos": len(candidatos),
        "total_postings_consultadas": total_postings_consultadas,
        "tempo_busca_segundos": tempo,
    }
    return candidatos, metricas


# ==============================================================================
# 5. CONTRATOS E PONTOS DE EXTENSÃO — MERGE SORT E TOP-K
# ==============================================================================

def merge(esquerda: list[dict], direita: list[dict], metricas: dict) -> list[dict]:
    """Procedimento de intercalação do Merge Sort.
    
    Critério determinístico obrigatório:
        1. Maior score primeiro (ordem decrescente de score);
        2. Em caso de empate no score, menor id_chunk primeiro (ordem lexicográfica crescente).
    """
    resultado = []
    i = j = 0

    while i < len(esquerda) and j < len(direita):
        metricas["comparacoes_totais"] += 1
        metricas["comparacoes_score"] += 1

        if esquerda[i]["score"] > direita[j]["score"]:
            resultado.append(esquerda[i])
            i += 1
        elif esquerda[i]["score"] < direita[j]["score"]:
            resultado.append(direita[j])
            j += 1
        else:
            metricas["empates_score"] += 1
            metricas["comparacoes_totais"] += 1
            metricas["comparacoes_id_chunk"] += 1

            if esquerda[i]["id_chunk"] <= direita[j]["id_chunk"]:
                resultado.append(esquerda[i])
                i += 1
            else:
                resultado.append(direita[j])
                j += 1

        metricas["movimentacoes"] += 1
    
    while i < len(esquerda):
        resultado.append(esquerda[i])
        i += 1
        metricas["movimentacoes"] += 1

    while j < len(direita):
        resultado.append(direita[j])
        j += 1
        metricas["movimentacoes"] += 1

    return resultado


def merge_sort(candidatos: list[dict], metricas: dict, profundidade: int = 1) -> list[dict]:
    """Ordenação dos candidatos via Merge Sort manual.
    
    Especificações teóricas:
        - Recorrência: T(N) = 2T(N/2) + Θ(N)
        - Complexidade temporal: Θ(N log N)
        - Espaço auxiliar: Θ(N)
        - É expressamente proibido o uso de sorted() ou list.sort() na versão final.
    """

    metricas["chamadas_recursivas"] += 1

    metricas["profundidade_maxima"] = max(
        metricas["profundidade_maxima"],
        profundidade
    )

    tamanho = len(candidatos)

    if tamanho <= 1:
        return candidatos

    meio = tamanho // 2
    esquerda = merge_sort(candidatos[:meio], metricas, profundidade + 1)
    direita = merge_sort(candidatos[meio:], metricas, profundidade + 1)

    return merge(esquerda, direita, metricas)


def selecionar_topk(candidatos_ordenados: list[dict], k: int) -> list[dict]:
    """Seleciona os k melhores resultados a partir dos candidatos ordenados.
    
    Se k > len(candidatos_ordenados), deve retornar todos os candidatos disponíveis.
    """

    return candidatos_ordenados[:k]


# ==============================================================================
# 6. SERIALIZAÇÃO E UTILITÁRIOS
# ==============================================================================

def serializar_json_compacto(objeto: dict) -> str:
    """Serializa o JSON mantendo listas de inteiros simples (ex: '[1, 2]') em linha única."""
    texto_json = json.dumps(objeto, ensure_ascii=False, indent=2)
    texto_json = re.sub(
        r'"paginas":\s*\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]',
        lambda m: f'"paginas": [{", ".join(re.findall(r"\d+", m.group(1)))}]',
        texto_json,
    )
    return texto_json + "\n"


def salvar_artefato(caminho: Path, dados: dict) -> None:
    """Grava um arquivo JSON com encoding UTF-8."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(serializar_json_compacto(dados), encoding="utf-8")


def executar_busca_modo(
    modo: str,
    consulta: str,
    k: int,
    chunks: list[dict],
    indice_invertido: dict,
    chunks_map: dict[str, dict],
    caminho_candidatos: Path,
    caminho_relatorio: Path,
    metrica: str = "bm25",
    k1: float = 1.5,
    b: float = 0.75,
    estatisticas_corpus: tuple[int, float, dict[str, int]] | None = None,
) -> tuple[list[dict], dict]:
    """Executa a busca (linear ou indexada) com a métrica configurada e grava os artefatos."""
    if modo == "linear":
        candidatos, metricas = buscar_linear(
            chunks,
            consulta,
            metrica=metrica,
            k1=k1,
            b=b,
            estatisticas_corpus=estatisticas_corpus,
        )
    else:
        candidatos, metricas = buscar_indexada(
            indice_invertido,
            chunks_map,
            consulta,
            metrica=metrica,
            k1=k1,
            b=b,
            estatisticas_corpus=estatisticas_corpus,
        )

    if metrica == "bm25":
        desc_criterio = f"Okapi BM25 com saturacao de TF e ponderacao por IDF (k1={k1}, b={b})"
    else:
        desc_criterio = "soma das frequencias dos termos distintos da consulta (apos remocao de stopwords NLTK) no chunk"

    saida_candidatos = {
        "metadados": {
            "etapa": "4_busca_lexical_candidatos",
            "proxima_acao": "Merge Sort manual e Top-k",
            "consulta": consulta,
            "k_solicitado": k,
            "configuracao": modo,
            "metrica_score": metrica,
            "criterio_score": desc_criterio,
            "criterio_desempate_esperado": "maior score decrescente, menor id_chunk crescente",
            **metricas,
        },
        "candidatos": candidatos,
    }

    relatorio = {
        "status_etapa": "concluido",
        "arquivo_candidatos_gerado": str(caminho_candidatos),
        "consulta": consulta,
        "k": k,
        "configuracao": modo,
        "metrica_score": metrica,
        **metricas,
    }

    salvar_artefato(caminho_candidatos, saida_candidatos)
    salvar_artefato(caminho_relatorio, relatorio)

    print("-" * 70)
    print(f"Configuração: {modo.upper()} | Métrica: {metrica.upper()}")
    print(f"Chunks no corpus: {len(chunks)}")
    print(f"Stopwords removidas (NLTK): {metricas.get('stopwords_removidas', [])}")
    print(f"Termos após filtro de stopwords: {metricas.get('termos_distintos_consulta', [])}")
    if metrica == "bm25":
        print(f"Parâmetros BM25: k1={k1}, b={b}, avgdl={metricas['parametros_metrica']['avgdl']}")
        print(f"IDFs calculados: {metricas.get('inverse_document_frequencies', {})}")
    print(f"Candidatos com score > 0: {len(candidatos)}")
    print(f"Tempo de busca: {metricas['tempo_busca_segundos']:.6f}s")
    if "total_comparacoes_termos" in metricas:
        print(f"Total de comparações de termos: {metricas['total_comparacoes_termos']}")
    if "total_postings_consultadas" in metricas:
        print(f"Total de postings consultadas: {metricas['total_postings_consultadas']}")
    print(f"Arquivo de candidatos gerado: {caminho_candidatos}")
    print(f"Arquivo de relatório gerado: {caminho_relatorio}")

    return candidatos, metricas

def executar_ordenacao(
    candidatos: list[dict], 
    k: int,
    caminho_candidatos_ordenados: str,
    caminho_topk: str,
    caminho_relatorio: str,
) -> list[dict]:
    """
    Executa a ordenação dos candidatos utilizando Merge Sort e retorna o Top-k.

    Parâmetros:
    - candidatos: Lista de dicionários representando os candidatos.
    - k: Número de resultados desejados para o Top-k.
    - caminho_candidatos_ordenados: Caminho para salvar o arquivo com os candidatos ordenados.
    - caminho_topk: Caminho para salvar o arquivo com os resultados do Top-k.
    - caminho_relatorio: Caminho para salvar o arquivo de relatório.

    Retorna:
    - top_k: Lista dos Top-k candidatos ordenados.
    """

    metricas = {
        "movimentacoes": 0,
        "chamadas_recursivas": 0,
        "profundidade_maxima": 0,
        "empates_score": 0,
        "comparacoes_score": 0,
        "comparacoes_id_chunk": 0,
        "comparacoes_totais": 0,
    };

    tracemalloc.start()
    inicio = time.perf_counter()
    candidatos_ordenados = merge_sort(candidatos, metricas)
    fim = time.perf_counter()

    _, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metricas["tempo_execucao"] = fim - inicio
    metricas["memoria_pico_bytes"] = memoria_pico

    saida_candidatos_ordenados = {
        "metadados": {
            "etapa": "4_busca_lexical_candidatos",
            "arquivo_candidatos_gerado": str(caminho_candidatos_ordenados),
            "proxima_acao": "Top-k",
            "tempo_ordenacao_segundos": metricas["tempo_execucao"],
            "num_candidatos_ordenados": len(candidatos_ordenados),
            "memoria_pico_bytes": metricas["memoria_pico_bytes"],
            "num_movimentacoes": metricas.get("movimentacoes", 0),
            "num_chamadas_recursivas": metricas.get("chamadas_recursivas", 0),
            "profundidade_maxima": metricas.get("profundidade_maxima", 0),
            "num_empates_score": metricas.get("empates_score", 0),
            "num_comparacoes_score": metricas.get("comparacoes_score", 0),
            "num_comparacoes_id_chunk": metricas.get("comparacoes_id_chunk", 0),
            "num_comparacoes_totais": metricas.get("comparacoes_totais", 0)
        },
        "candidatos_ordenados": candidatos_ordenados,
    }
    salvar_artefato(caminho_candidatos_ordenados, saida_candidatos_ordenados)

    top_k = selecionar_topk(candidatos_ordenados, k)
    saida_topk = {
        "metadados": {
            "etapa": "4_busca_lexical_candidatos",
            "proxima_acao": "Resultados",
            "tempo_ordenacao_segundos": metricas["tempo_execucao"],
            "num_top_k": len(top_k),
        },
        "top_k_candidatos": top_k,
    }
    salvar_artefato(caminho_topk, saida_topk)

    salvar_artefato(caminho_relatorio, {
        "status_etapa": "concluido",
        "arquivo_candidatos_gerado": str(caminho_candidatos_ordenados),
        "tempo_ordenacao_segundos": metricas["tempo_execucao"],
        "num_candidatos_ordenados": len(candidatos_ordenados),
        "num_top_k": len(top_k),
        "k": k,
        "memoria_pico_bytes": metricas["memoria_pico_bytes"],
        "num_movimentacoes": metricas.get("movimentacoes", 0),
        "num_chamadas_recursivas": metricas.get("chamadas_recursivas", 0),
        "profundidade_maxima": metricas.get("profundidade_maxima", 0),
        "num_empates_score": metricas.get("empates_score", 0),
        "num_comparacoes_score": metricas.get("comparacoes_score", 0),
        "num_comparacoes_id_chunk": metricas.get("comparacoes_id_chunk", 0),
        "num_comparacoes_totais": metricas.get("comparacoes_totais", 0)
    })

    print("-" * 70)
    print(f"Top-{k} candidatos ordenados gerados com sucesso.")
    print(f"Arquivo de candidatos ordenados: {caminho_candidatos_ordenados}")
    print(f"Arquivo de Top-{k}: {caminho_topk}")
    print(f"Arquivo de relatório gerado: {caminho_relatorio}")

    return top_k

# ==============================================================================
# 7. EXECUÇÃO PRINCIPAL (CLI)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Etapa 4 — Busca Lexical, Score (BM25 / Simples) e Geração de Candidatos."
    )
    parser.add_argument(
        "--consulta",
        type=str,
        default="critérios para atribuição de bolsas",
        help="Consulta textual para busca nos chunks.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Número de resultados desejados para o Top-k (padrão: 5).",
    )
    parser.add_argument(
        "--modo",
        choices=["indexada", "linear", "ambos"],
        default="indexada",
        help="Estratégia de busca a ser utilizada: 'indexada', 'linear' ou 'ambos' (padrão: indexada).",
    )
    parser.add_argument(
        "--metrica",
        choices=["bm25", "simples"],
        default="bm25",
        help="Métrica de pontuação de relevância: 'bm25' (Okapi BM25) ou 'simples' (contagem linear) (padrão: bm25).",
    )
    parser.add_argument(
        "--k1",
        type=float,
        default=1.5,
        help="Parâmetro k1 do BM25 (controla a saturação do TF; padrão: 1.5).",
    )
    parser.add_argument(
        "--b",
        type=float,
        default=0.75,
        help="Parâmetro b do BM25 (controla a normalização pelo tamanho do chunk; padrão: 0.75).",
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=Path("4_chunks/chunks.json"),
        help="Caminho do arquivo com os chunks gerados na Etapa 2.",
    )
    parser.add_argument(
        "--indice",
        type=Path,
        default=Path("5_indexacao/indice_invertido.json"),
        help="Caminho do arquivo com o índice invertido gerado na Etapa 3.",
    )
    parser.add_argument(
        "--saida-candidatos",
        type=Path,
        default=None,
        help="Caminho customizado para gravação dos candidatos (se omitido, deriva do modo).",
    )
    parser.add_argument(
        "--relatorio-busca",
        type=Path,
        default=None,
        help="Caminho customizado para gravação do relatório (se omitido, deriva do modo).",
    )
    parser.add_argument(
        "--saida_candidatos_ordenados",
        type=Path,
        default=None,
        help="Caminho customizado para gravação dos candidatos ordenados (se omitido, deriva do modo).",
    )
    parser.add_argument(
        "--saida_candidatos_top_k",
        type=Path,
        default=None,
        help="Caminho customizado para gravação dos candidatos top k (se omitido, deriva do modo).",
    )
    parser.add_argument(
        "--relatorio-ordenacao",
        type=Path,
        default=None,
        help="Caminho customizado para gravação do relatório de ordenação (se omitido, deriva do modo).",
    )
    args = parser.parse_args()

    # Validação dos parâmetros de entrada e casos de borda
    if args.k < 1:
        raise ValueError(f"O parâmetro k deve ser maior ou igual a 1. Valor recebido: {args.k}")
    if args.k1 < 0:
        raise ValueError(f"O hiperparâmetro k1 do BM25 deve ser >= 0. Valor recebido: {args.k1}")
    if not (0.0 <= args.b <= 1.0):
        raise ValueError(f"O hiperparâmetro b do BM25 deve estar no intervalo [0, 1]. Valor recebido: {args.b}")

    if not args.chunks.exists():
        raise FileNotFoundError(f"Arquivo de chunks não encontrado: {args.chunks}")

    dados_chunks = json.loads(args.chunks.read_text(encoding="utf-8"))
    chunks = dados_chunks.get("chunks", [])
    if not chunks:
        raise ValueError("Nenhum chunk válido encontrado em 4_chunks/chunks.json.")

    chunks_map = {chunk["id_chunk"]: chunk for chunk in chunks}

    indice_invertido = {}
    if args.modo in ("indexada", "ambos"):
        if not args.indice.exists():
            raise FileNotFoundError(f"Arquivo de índice invertido não encontrado: {args.indice}")
        dados_indice = json.loads(args.indice.read_text(encoding="utf-8"))
        indice_invertido = dados_indice.get("indice_invertido", {})

    # Estatísticas globais do corpus computadas uma única vez
    estatisticas_corpus = calcular_estatisticas_corpus(chunks)

    print("=" * 70)
    print("ETAPA 4 — BUSCA LEXICAL E GERAÇÃO DE CANDIDATOS")
    print("=" * 70)
    print(f"Consulta: '{args.consulta}'")
    print(f"Valor de k: {args.k}")
    print(f"Métrica de Relevância: {args.metrica.upper()}")
    if args.metrica == "bm25":
        print(f"Hiperparâmetros BM25: k1={args.k1}, b={args.b}")

    if args.modo == "indexada":
        caminho_cand = args.saida_candidatos or Path("6_busca_lexical/candidatos_busca.json")
        caminho_rel = args.relatorio_busca or Path("6_busca_lexical/relatorio_busca.json")
        candidatos, metricas = executar_busca_modo(
            "indexada",
            args.consulta,
            args.k,
            chunks,
            indice_invertido,
            chunks_map,
            caminho_cand,
            caminho_rel,
            metrica=args.metrica,
            k1=args.k1,
            b=args.b,
            estatisticas_corpus=estatisticas_corpus,
        )

    elif args.modo == "linear":
        caminho_cand = args.saida_candidatos or Path("6_busca_lexical/candidatos_linear.json")
        caminho_rel = args.relatorio_busca or Path("6_busca_lexical/relatorio_busca_linear.json")
        candidatos, metricas = executar_busca_modo(
            "linear",
            args.consulta,
            args.k,
            chunks,
            indice_invertido,
            chunks_map,
            caminho_cand,
            caminho_rel,
            metrica=args.metrica,
            k1=args.k1,
            b=args.b,
            estatisticas_corpus=estatisticas_corpus,
        )

    elif args.modo == "ambos":
        caminho_cand_lin = Path("6_busca_lexical/candidatos_linear.json")
        caminho_rel_lin = Path("6_busca_lexical/relatorio_busca_linear.json")
        caminho_cand_idx = Path("6_busca_lexical/candidatos_indexada.json")
        caminho_rel_idx = Path("6_busca_lexical/relatorio_busca_indexada.json")
        candidatos, metricas = executar_busca_modo(
            "linear",
            args.consulta,
            args.k,
            chunks,
            indice_invertido,
            chunks_map,
            caminho_cand_lin,
            caminho_rel_lin,
            metrica=args.metrica,
            k1=args.k1,
            b=args.b,
            estatisticas_corpus=estatisticas_corpus,
        )
        executar_busca_modo(
            "indexada",
            args.consulta,
            args.k,
            chunks,
            indice_invertido,
            chunks_map,
            caminho_cand_idx,
            caminho_rel_idx,
            metrica=args.metrica,
            k1=args.k1,
            b=args.b,
            estatisticas_corpus=estatisticas_corpus,
        )

    print("=" * 70)
    print("Pronto para leitura do arquivo de candidatos ('candidatos_busca.json'),")
    print("aplicação do Merge Sort manual e geração dos Top-k.")
    print("=" * 70)

    caminho_candidatos_ordenados = args.saida_candidatos_ordenados or Path("6_busca_lexical/candidatos_ordenados.json")
    caminho_topk = args.saida_candidatos_top_k or Path("6_busca_lexical/candidatos_topk.json")
    caminho_relatorio = args.relatorio_ordenacao or Path("6_busca_lexical/relatorio_ordenacao.json")
    executar_ordenacao(
        candidatos,
        args.k,
        caminho_candidatos_ordenados,
        caminho_topk,
        caminho_relatorio,
    )

if __name__ == "__main__":
    main()
