export interface DocumentoCatalogo {
  id_documento: string;
  nome_arquivo: string;
  caminho_relativo: string;
  tamanho_bytes: number;
  hash_sha256: string;
  quantidade_paginas: number;
  fonte_url: string;
  status_processamento: string;
}

export interface PaginaNormalizada {
  numero_pagina: number;
  texto_normalizado: string;
  status_normalizacao: string;
  motivo_status?: string;
}

export interface DocumentoNormalizado {
  id_documento: string;
  nome_arquivo: string;
  paginas: PaginaNormalizada[];
}

export interface Chunk {
  id_chunk: string;
  id_documento: string;
  nome_arquivo: string;
  paginas: number[];
  ordem_chunk_documento: number;
  ordem_global: number;
  inicio_palavra: number;
  fim_palavra: number;
  quantidade_palavras: number;
  quantidade_caracteres: number;
  texto: string;
}

export interface PostingItem {
  id_chunk: string;
  frequencia: number;
}

export interface TermoIndice {
  chunks: PostingItem[];
  frequencia_total: number;
}

export interface IndiceInvertidoData {
  metadados: {
    estrategia: string;
    regras_tokenizacao: string[];
    total_chunks_entrada: number;
    total_termos: number;
    total_postings: number;
    total_ocorrencias: number;
    tempo_construcao_segundos: number;
  };
  indice_invertido: Record<string, TermoIndice>;
}

export interface RelatorioProcessamento {
  status_pipeline: string;
  quantidade_documentos: number;
  quantidade_paginas: number;
  quantidade_paginas_vazias: number;
  tempo_processamento_segundos: number;
  regras_normalizacao: string[];
  avisos: Array<{
    id_documento: string;
    nome_arquivo: string;
    paginas_vazias: Array<{
      numero_pagina: number;
      motivo_status: string;
    }>;
  }>;
}

export interface RelatorioChunking {
  status_etapa: string;
  total_documentos: number;
  total_chunks: number;
  chunks_com_overlap_entre_paginas: number;
  percentual_chunks_cruzam_paginas: number;
  parametros: {
    tamanho_chunk_palavras: number;
    overlap_palavras: number;
    passo_palavras: number;
  };
  estatisticas_palavras: {
    media: number;
    minimo: number;
    maximo: number;
    total_palavras_acumuladas: number;
  };
  tempo_execucao_segundos: number;
  documentos: Array<{
    id_documento: string;
    nome_arquivo: string;
    paginas_com_conteudo: number;
    quantidade_chunks: number;
    chunks_com_overlap_entre_paginas: number;
  }>;
}

export interface RelatorioIndexacao {
  status_etapa: string;
  estrategia: string;
  regras_tokenizacao: string[];
  total_chunks_entrada: number;
  total_termos: number;
  total_postings: number;
  total_ocorrencias: number;
  tempo_construcao_segundos: number;
  entrada: string;
  saida: string;
}

export interface SearchResultItem {
  chunk: Chunk;
  score: number;
  termosEncontrados: { termo: string; frequencia: number }[];
  termosCoincidentes: number;
}

export interface SearchMetrics {
  tempoBuscaMs: number;
  tempoOrdenacaoMs: number;
  totalComparacoesMergeSort: number;
  candidatosEncontrados: number;
  termosConsultados: string[];
}
