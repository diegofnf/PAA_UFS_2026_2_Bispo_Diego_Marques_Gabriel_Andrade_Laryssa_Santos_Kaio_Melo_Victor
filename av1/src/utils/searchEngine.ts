/**
 * Motor de busca lexical com Okapi BM25 e seleção Top-k.
 *
 * Reproduz **exatamente** a semântica de `1_scripts/4_buscar_e_ordenar.py` (Etapa 4),
 * para que os números exibidos na aplicação web coincidam com os artefatos
 * versionados em `6_busca_lexical/` e `7_resultados/`:
 *
 * - Tokenização Unicode NFC + casefold com `[^\W_]+` (acentos preservados);
 * - Remoção de stopwords em português do NLTK;
 * - `|D|` e `avgdl` medidos em **tokens do texto** do chunk (não em
 *   `quantidade_palavras`, que é o campo do *chunking*);
 * - `IDF(t) = ln(1 + (N - DF(t) + 0.5) / (DF(t) + 0.5))`;
 * - `TF_BM25 = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * |D| / avgdl))`;
 * - Ordenação por Merge Sort com critério `(-score, id_chunk)`.
 */

import { Chunk, IndiceInvertidoData, SearchResultItem, SearchMetrics } from '../types';
import { tokenizar } from './tokenizer';
import { filtrarStopwords } from './stopwords';
import { mergeSort } from './mergeSort';

export interface SearchOptions {
  modo: 'OU' | 'E';
  metrica: 'bm25' | 'frequencia';
  k: number;
  k1?: number;
  b?: number;
  idDocumentoFiltro?: string;
}

export const K1_PADRAO = 1.5;
export const B_PADRAO = 0.75;

function calcularIdfBm25(totalDocumentos: number, docFreq: number): number {
  if (totalDocumentos <= 0 || docFreq <= 0) return 0;
  return Math.log(1 + (totalDocumentos - docFreq + 0.5) / (docFreq + 0.5));
}

function calcularTfBm25(freq: number, docLen: number, avgdl: number, k1: number, b: number): number {
  if (freq <= 0) return 0;
  const ajusteTamanho = 1 - b + (avgdl > 0 ? b * (docLen / avgdl) : 0);
  const denominador = freq + k1 * ajusteTamanho;
  if (denominador <= 0) return 0;
  return (freq * (k1 + 1)) / denominador;
}

export function executarBuscaLexical(
  consulta: string,
  chunksMap: Map<string, Chunk>,
  indiceData: IndiceInvertidoData,
  opcoes: SearchOptions
): { resultados: SearchResultItem[]; metricas: SearchMetrics } {
  const k1 = opcoes.k1 ?? K1_PADRAO;
  const b = opcoes.b ?? B_PADRAO;
  const tInicioBusca = performance.now();

  const tokensConsulta = tokenizar(consulta);
  const { termosDistintos, removidas: stopwordsRemovidas } = filtrarStopwords(tokensConsulta);

  if (termosDistintos.length === 0) {
    return {
      resultados: [],
      metricas: {
        tempoBuscaMs: 0,
        tempoOrdenacaoMs: 0,
        totalComparacoesMergeSort: 0,
        candidatosEncontrados: 0,
        termosConsultados: [],
        stopwordsRemovidas,
        termosAposFiltro: [],
      },
    };
  }

  const chunksLista = Array.from(chunksMap.values());
  const N = indiceData.metadados.total_chunks_entrada || chunksLista.length || 182;

  // |D| e avgdl precisam ser medidos sobre os tokens do texto, como no script Python.
  const comprimentosDoc = new Map<string, number>();
  let totalTokens = 0;
  for (const chunk of chunksLista) {
    const tamanho = tokenizar(chunk.texto).length;
    comprimentosDoc.set(chunk.id_chunk, tamanho);
    totalTokens += tamanho;
  }
  const avgdl = N > 0 ? totalTokens / N : 0;

  const pontuacoes = new Map<
    string,
    {
      chunk: Chunk;
      score: number;
      termosEncontrados: { termo: string; frequencia: number }[];
    }
  >();

  for (const termo of termosDistintos) {
    const registroTermo = indiceData.indice_invertido[termo];
    if (!registroTermo) continue;

    const idf = calcularIdfBm25(N, registroTermo.chunks.length);

    for (const posting of registroTermo.chunks) {
      const chunk = chunksMap.get(posting.id_chunk);
      if (!chunk) continue;

      if (opcoes.idDocumentoFiltro && chunk.id_documento !== opcoes.idDocumentoFiltro) {
        continue;
      }

      let entry = pontuacoes.get(chunk.id_chunk);
      if (!entry) {
        entry = { chunk, score: 0, termosEncontrados: [] };
        pontuacoes.set(chunk.id_chunk, entry);
      }

      entry.termosEncontrados.push({ termo, frequencia: posting.frequencia });

      if (opcoes.metrica === 'bm25') {
        const docLen = comprimentosDoc.get(chunk.id_chunk) ?? 0;
        entry.score += idf * calcularTfBm25(posting.frequencia, docLen, avgdl, k1, b);
      } else {
        entry.score += posting.frequencia;
      }
    }
  }

  const candidatosLista: SearchResultItem[] = [];
  const totalTermosDistintos = termosDistintos.length;

  for (const entry of pontuacoes.values()) {
    const termosPresentes = new Set(entry.termosEncontrados.map((t) => t.termo)).size;
    if (opcoes.modo === 'E' && termosPresentes < totalTermosDistintos) {
      continue;
    }
    candidatosLista.push({
      chunk: entry.chunk,
      score: Number(entry.score.toFixed(4)),
      termosEncontrados: entry.termosEncontrados,
      termosCoincidentes: termosPresentes,
    });
  }

  const tempoFimBusca = performance.now();
  const tempoBuscaMs = Number((tempoFimBusca - tInicioBusca).toFixed(3));

  // Ordenação usando Merge Sort (Etapa 4 - PAA).
  // Critério da Etapa 4: score decrescente; desempate por id_chunk ascendente.
  const mergeResult = mergeSort(candidatosLista, {
    compararScore: (a, b2) => b2.score - a.score,
    desempatar: (a, b2) =>
      a.chunk.id_chunk < b2.chunk.id_chunk ? -1 : a.chunk.id_chunk > b2.chunk.id_chunk ? 1 : 0,
  });

  // Top-k fatiamento
  const topKResultados = opcoes.k > 0 ? mergeResult.sorted.slice(0, opcoes.k) : mergeResult.sorted;

  return {
    resultados: topKResultados,
    metricas: {
      tempoBuscaMs,
      tempoOrdenacaoMs: mergeResult.tempoMs,
      totalComparacoesMergeSort: mergeResult.comparacoes,
      candidatosEncontrados: candidatosLista.length,
      termosConsultados: termosDistintos,
      stopwordsRemovidas,
      termosAposFiltro: termosDistintos,
    },
  };
}
