import { Chunk, IndiceInvertidoData, SearchResultItem, SearchMetrics } from '../types';
import { tokenizar } from './tokenizer';
import { mergeSort } from './mergeSort';

export interface SearchOptions {
  modo: 'OU' | 'E';
  metrica: 'tf_idf' | 'frequencia';
  k: number;
  idDocumentoFiltro?: string;
}

export function executarBuscaLexical(
  consulta: string,
  chunksMap: Map<string, Chunk>,
  indiceData: IndiceInvertidoData,
  opcoes: SearchOptions
): { resultados: SearchResultItem[]; metricas: SearchMetrics } {
  const tInicioBusca = performance.now();
  const tokens = tokenizar(consulta);

  if (tokens.length === 0) {
    return {
      resultados: [],
      metricas: {
        tempoBuscaMs: 0,
        tempoOrdenacaoMs: 0,
        totalComparacoesMergeSort: 0,
        candidatosEncontrados: 0,
        termosConsultados: [],
      },
    };
  }

  const N = indiceData.metadados.total_chunks_entrada || chunksMap.size || 182;
  const candidatosMap = new Map<
    string,
    {
      chunk: Chunk;
      score: number;
      termosEncontrados: { termo: string; frequencia: number }[];
    }
  >();

  // Processa cada token de consulta usando o índice invertido
  for (const termo of tokens) {
    const registroTermo = indiceData.indice_invertido[termo];
    if (!registroTermo) continue;

    const df = registroTermo.chunks.length;
    // IDF calculado com suavização típica BM25/TF-IDF
    const idf = Math.log(1 + (N - df + 0.5) / (df + 0.5));

    for (const posting of registroTermo.chunks) {
      const chunk = chunksMap.get(posting.id_chunk);
      if (!chunk) continue;

      // Filtro opcional por documento
      if (opcoes.idDocumentoFiltro && chunk.id_documento !== opcoes.idDocumentoFiltro) {
        continue;
      }

      let entry = candidatosMap.get(chunk.id_chunk);
      if (!entry) {
        entry = {
          chunk,
          score: 0,
          termosEncontrados: [],
        };
        candidatosMap.set(chunk.id_chunk, entry);
      }

      entry.termosEncontrados.push({
        termo,
        frequencia: posting.frequencia,
      });

      if (opcoes.metrica === 'tf_idf') {
        const tf = posting.frequencia / (chunk.quantidade_palavras || 1);
        entry.score += tf * idf;
      } else {
        entry.score += posting.frequencia;
      }
    }
  }

  // Filtragem conforme o modo booleano ('E' vs 'OU')
  const candidatosLista: SearchResultItem[] = [];
  const totalTokensUnicos = new Set(tokens).size;

  for (const entry of candidatosMap.values()) {
    const termosPresentes = new Set(entry.termosEncontrados.map((t) => t.termo)).size;
    if (opcoes.modo === 'E' && termosPresentes < totalTokensUnicos) {
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

  // Ordenação usando Merge Sort (Etapa 4 - PAA)
  // Critério primário: maior score. Critério secundário: maior quantidade de termos coincidentes.
  // Critério terciário de desempate: ID do chunk ascendente.
  const mergeResult = mergeSort(candidatosLista, (a, b) => {
    if (b.score !== a.score) {
      return b.score - a.score;
    }
    if (b.termosCoincidentes !== a.termosCoincidentes) {
      return b.termosCoincidentes - a.termosCoincidentes;
    }
    return a.chunk.id_chunk.localeCompare(b.chunk.id_chunk);
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
      termosConsultados: tokens,
    },
  };
}
