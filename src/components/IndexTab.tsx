import React, { useState, useMemo } from 'react';
import {
  Hash,
  Search,
  FileText,
  TrendingUp,
  Flame,
  Layers,
  LayoutGrid,
  Info,
  ExternalLink,
} from 'lucide-react';
import { Chunk, DocumentoCatalogo, IndiceInvertidoData } from '../types';

interface IndexTabProps {
  indiceData: IndiceInvertidoData | null;
  chunksMap: Map<string, Chunk>;
  chunks?: Chunk[];
  documentos?: DocumentoCatalogo[];
}

export const IndexTab: React.FC<IndexTabProps> = ({
  indiceData,
  chunksMap,
  chunks = [],
  documentos = [],
}) => {
  const [filtroTermo, setFiltroTermo] = useState('');
  const [termoSelecionado, setTermoSelecionado] = useState<string>('mestrado');
  const [paginaTermos, setPaginaTermos] = useState(1);
  const [modoVisualizacao, setModoVisualizacao] = useState<'documentos' | 'fita'>('documentos');
  const [chunkInspecionadoId, setChunkInspecionadoId] = useState<string | null>(null);

  const termosPorPagina = 24;
  const metadados = indiceData?.metadados;

  // Lista ordenada de chunks (182 chunks)
  const todosChunks = useMemo(() => {
    if (chunks.length > 0) return chunks;
    return Array.from(chunksMap.values()).sort((a, b) => a.ordem_global - b.ordem_global);
  }, [chunks, chunksMap]);

  // Top mais frequentes do corpus
  const topTermos = useMemo(() => {
    if (!indiceData) return [];
    return Object.entries(indiceData.indice_invertido)
      .map(([termo, dados]) => ({
        termo,
        frequencia_total: dados.frequencia_total,
        total_chunks: dados.chunks.length,
      }))
      .sort((a, b) => b.frequencia_total - a.frequencia_total)
      .slice(0, 30);
  }, [indiceData]);

  const termosFiltrados = useMemo(() => {
    if (!indiceData) return [];
    const todos = Object.keys(indiceData.indice_invertido).sort();
    if (!filtroTermo.trim()) return todos;
    const q = filtroTermo.toLowerCase();
    return todos.filter((t) => t.includes(q));
  }, [indiceData, filtroTermo]);

  const totalPaginas = Math.ceil(termosFiltrados.length / termosPorPagina) || 1;
  const termosExibidos = useMemo(() => {
    const inicio = (paginaTermos - 1) * termosPorPagina;
    return termosFiltrados.slice(inicio, inicio + termosPorPagina);
  }, [termosFiltrados, paginaTermos]);

  const dadosTermoSelecionado = useMemo(() => {
    if (!indiceData || !termoSelecionado) return null;
    return indiceData.indice_invertido[termoSelecionado] || null;
  }, [indiceData, termoSelecionado]);

  // Mapa rápido de frequência do termo por ID de chunk
  const frequenciaPorChunk = useMemo(() => {
    const map = new Map<string, number>();
    if (dadosTermoSelecionado) {
      dadosTermoSelecionado.chunks.forEach((posting) => {
        map.set(posting.id_chunk, posting.frequencia);
      });
    }
    return map;
  }, [dadosTermoSelecionado]);

  // Estatísticas de densidade do termo selecionado
  const estatisticasTermo = useMemo(() => {
    if (!dadosTermoSelecionado) {
      return {
        totalOcorrencias: 0,
        chunksComOcorrencia: 0,
        taxaCobertura: 0,
        picoFrequencia: 0,
        picoChunkId: null as string | null,
        documentoDestaque: null as string | null,
      };
    }

    const totalOcorrencias = dadosTermoSelecionado.frequencia_total;
    const chunksComOcorrencia = dadosTermoSelecionado.chunks.length;
    const taxaCobertura = todosChunks.length > 0
      ? ((chunksComOcorrencia / todosChunks.length) * 100).toFixed(1)
      : '0.0';

    let picoFrequencia = 0;
    let picoChunkId: string | null = null;
    const ocorrenciasPorDoc = new Map<string, number>();

    dadosTermoSelecionado.chunks.forEach((p) => {
      if (p.frequencia > picoFrequencia) {
        picoFrequencia = p.frequencia;
        picoChunkId = p.id_chunk;
      }
      const chunk = chunksMap.get(p.id_chunk);
      if (chunk) {
        const docId = chunk.id_documento;
        ocorrenciasPorDoc.set(docId, (ocorrenciasPorDoc.get(docId) || 0) + p.frequencia);
      }
    });

    let docDestaqueId: string | null = null;
    let maxDocOcorrencias = 0;
    ocorrenciasPorDoc.forEach((qtd, idDoc) => {
      if (qtd > maxDocOcorrencias) {
        maxDocOcorrencias = qtd;
        docDestaqueId = idDoc;
      }
    });

    return {
      totalOcorrencias,
      chunksComOcorrencia,
      taxaCobertura,
      picoFrequencia,
      picoChunkId,
      documentoDestaque: docDestaqueId
        ? `${docDestaqueId} (${maxDocOcorrencias}x)`
        : null,
    };
  }, [dadosTermoSelecionado, todosChunks, chunksMap]);

  // Agrupamento dos chunks por documento para o Mapa de Calor
  const documentosComChunks = useMemo(() => {
    const mapa = new Map<
      string,
      {
        id_documento: string;
        nome_arquivo: string;
        chunks: Chunk[];
        totalOcorrencias: number;
        chunksComTermo: number;
      }
    >();

    // Inicializa pelos documentos do catálogo para preservar a ordem oficial
    documentos.forEach((doc) => {
      mapa.set(doc.id_documento, {
        id_documento: doc.id_documento,
        nome_arquivo: doc.nome_arquivo,
        chunks: [],
        totalOcorrencias: 0,
        chunksComTermo: 0,
      });
    });

    // Adiciona cada chunk ao seu documento correspondente
    todosChunks.forEach((chunk) => {
      if (!mapa.has(chunk.id_documento)) {
        mapa.set(chunk.id_documento, {
          id_documento: chunk.id_documento,
          nome_arquivo: chunk.nome_arquivo,
          chunks: [],
          totalOcorrencias: 0,
          chunksComTermo: 0,
        });
      }
      const entrada = mapa.get(chunk.id_documento)!;
      entrada.chunks.push(chunk);

      const freq = frequenciaPorChunk.get(chunk.id_chunk) || 0;
      if (freq > 0) {
        entrada.totalOcorrencias += freq;
        entrada.chunksComTermo += 1;
      }
    });

    return Array.from(mapa.values());
  }, [documentos, todosChunks, frequenciaPorChunk]);

  // Chunk ativo para inspeção imediata no heatmap
  const chunkInspecionado = useMemo(() => {
    if (!chunkInspecionadoId) {
      // Se não selecionou nenhum, sugere o chunk de maior pico
      if (estatisticasTermo.picoChunkId) {
        return chunksMap.get(estatisticasTermo.picoChunkId) || null;
      }
      return null;
    }
    return chunksMap.get(chunkInspecionadoId) || null;
  }, [chunkInspecionadoId, estatisticasTermo.picoChunkId, chunksMap]);

  // Função para aplicar estilos de calor conforme a densidade
  const getHeatmapColor = (freq: number) => {
    if (freq === 0) {
      return 'bg-slate-100 text-slate-400 border-slate-200/80 hover:bg-slate-200/70 hover:border-slate-300';
    }
    if (freq === 1) {
      return 'bg-amber-100 text-amber-900 border-amber-200 hover:bg-amber-200 font-medium shadow-2xs';
    }
    if (freq === 2) {
      return 'bg-amber-200 text-amber-950 border-amber-300 hover:bg-amber-300 font-semibold shadow-2xs';
    }
    if (freq <= 4) {
      return 'bg-amber-400 text-amber-950 border-amber-500 hover:bg-amber-500 font-bold shadow-2xs';
    }
    return 'bg-orange-600 text-white border-orange-700 hover:bg-orange-700 font-bold shadow-xs';
  };

  // Realce do termo selecionado no trecho de texto
  const highlightTermo = (texto: string, termo: string) => {
    if (!termo.trim()) return texto;
    const regex = new RegExp(`(${termo})`, 'gi');
    const partes = texto.split(regex);
    return partes.map((parte, i) =>
      regex.test(parte) ? (
        <mark
          key={i}
          className="bg-amber-200 text-amber-950 font-bold px-1 rounded border-b border-amber-400"
        >
          {parte}
        </mark>
      ) : (
        parte
      )
    );
  };

  return (
    <div className="space-y-6">
      {/* Index Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Total de Termos (Vocabulário)</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {metadados?.total_termos.toLocaleString('pt-BR') ?? 5258}
          </div>
          <span className="text-[11px] text-sky-700 font-medium">Tokens alfanuméricos únicos</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Total de Postings</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {metadados?.total_postings.toLocaleString('pt-BR') ?? 19863}
          </div>
          <span className="text-[11px] text-emerald-700 font-medium">Pares (Termo, ID_Chunk)</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Total de Ocorrências</span>
          <div className="text-2xl font-bold text-amber-600 mt-1">
            {metadados?.total_ocorrencias.toLocaleString('pt-BR') ?? 35827}
          </div>
          <span className="text-[11px] text-slate-500">Palavras contadas no corpus</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Tempo de Construção</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {metadados?.tempo_construcao_segundos ?? 0.043}{' '}
            <span className="text-xs text-slate-500 font-normal">s</span>
          </div>
          <span className="text-[11px] text-slate-500">Indexação Python in-memory</span>
        </div>
      </div>

      {/* Top Terms Bar / Preview */}
      <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-4 h-4 text-sky-600" />
          <h3 className="text-sm font-semibold text-slate-900">Termos com Maior Frequência no Corpus</h3>
          <span className="text-xs text-slate-500">(Distribuição empírica estilo Lei de Zipf)</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {topTermos.map((item) => (
            <button
              key={item.termo}
              onClick={() => {
                setTermoSelecionado(item.termo);
                setChunkInspecionadoId(null);
              }}
              className={`text-xs px-2.5 py-1 rounded-lg border transition-all flex items-center gap-1.5 ${
                termoSelecionado === item.termo
                  ? 'bg-sky-600 text-white border-sky-600 shadow-2xs font-semibold'
                  : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              <span>{item.termo}</span>
              <span className="text-[10px] opacity-75 font-mono">
                {item.frequencia_total}x
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* MAPA DE CALOR DE DENSIDADE DO TERMO SELECIONADO */}
      <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs space-y-4">
        {/* Cabeçalho do Mapa de Calor */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 shrink-0">
              <Flame className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">
                  Mapa de Calor de Densidade:
                </h3>
                <span className="font-mono font-bold text-sm bg-sky-50 text-sky-800 border border-sky-200 px-2 py-0.5 rounded">
                  "{termoSelecionado}"
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Distribuição espacial de frequência em cada chunk indexado do corpus PROCC/UFS
              </p>
            </div>
          </div>

          {/* Alternador de visualização e Legenda */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
              <button
                onClick={() => setModoVisualizacao('documentos')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded transition-all ${
                  modoVisualizacao === 'documentos'
                    ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Agrupar células por documento normativo"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Por Regulamento</span>
              </button>
              <button
                onClick={() => setModoVisualizacao('fita')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded transition-all ${
                  modoVisualizacao === 'fita'
                    ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Visualização panorâmica sequencial de todos os 182 chunks"
              >
                <LayoutGrid className="w-3.5 h-3.5" />
                <span>Fita Panorâmica</span>
              </button>
            </div>
          </div>
        </div>

        {/* Resumo Numérico de Densidade */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
          <div>
            <span className="text-slate-500">Total no Corpus:</span>
            <div className="text-base font-bold text-slate-900 mt-0.5">
              {estatisticasTermo.totalOcorrencias} ocorrências
            </div>
          </div>
          <div>
            <span className="text-slate-500">Cobertura em Chunks:</span>
            <div className="text-base font-bold text-slate-900 mt-0.5">
              {estatisticasTermo.chunksComOcorrencia} de {todosChunks.length} ({estatisticasTermo.taxaCobertura}%)
            </div>
          </div>
          <div>
            <span className="text-slate-500">Pico em Chunk Único:</span>
            <div className="text-base font-bold text-amber-700 mt-0.5">
              {estatisticasTermo.picoFrequencia > 0
                ? `${estatisticasTermo.picoFrequencia}x (${estatisticasTermo.picoChunkId})`
                : '0'}
            </div>
          </div>
          <div>
            <span className="text-slate-500">Maior Concentração:</span>
            <div className="text-base font-bold text-sky-800 mt-0.5 truncate" title={estatisticasTermo.documentoDestaque || ''}>
              {estatisticasTermo.documentoDestaque || 'Sem ocorrências'}
            </div>
          </div>
        </div>

        {/* Legenda da Escala Térmica */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs pt-1">
          <span className="text-slate-500 font-medium">Escala de Intensidade:</span>
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-[11px]">
            <span className="flex items-center gap-1 text-slate-600">
              <span className="w-4 h-4 rounded bg-slate-100 border border-slate-300 inline-block" />
              0x
            </span>
            <span className="flex items-center gap-1 text-slate-600">
              <span className="w-4 h-4 rounded bg-amber-100 border border-amber-200 inline-block" />
              1x
            </span>
            <span className="flex items-center gap-1 text-slate-600">
              <span className="w-4 h-4 rounded bg-amber-200 border border-amber-300 inline-block" />
              2x
            </span>
            <span className="flex items-center gap-1 text-slate-600">
              <span className="w-4 h-4 rounded bg-amber-400 border border-amber-500 inline-block" />
              3-4x
            </span>
            <span className="flex items-center gap-1 text-slate-600">
              <span className="w-4 h-4 rounded bg-orange-600 border border-orange-700 inline-block" />
              5x+ (Hotspot)
            </span>
          </div>
        </div>

        {/* Conteúdo do Mapa: Modo Agrupado por Documento */}
        {modoVisualizacao === 'documentos' && (
          <div className="space-y-4 pt-2">
            {documentosComChunks.map((doc) => {
              const percTotal =
                estatisticasTermo.totalOcorrencias > 0
                  ? ((doc.totalOcorrencias / estatisticasTermo.totalOcorrencias) * 100).toFixed(1)
                  : '0.0';

              return (
                <div
                  key={doc.id_documento}
                  className="bg-slate-50/60 border border-slate-200 rounded-lg p-3 space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-1 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sky-700 bg-sky-100/70 border border-sky-200 px-1.5 py-0.5 rounded">
                        {doc.id_documento}
                      </span>
                      <span className="font-medium text-slate-800 truncate max-w-sm sm:max-w-md" title={doc.nome_arquivo}>
                        {doc.nome_arquivo}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] font-mono">
                      <span className="text-slate-500">
                        {doc.chunks.length} chunks
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded font-semibold ${
                          doc.totalOcorrencias > 0
                            ? 'bg-amber-100 text-amber-900 border border-amber-200'
                            : 'bg-slate-100 text-slate-400 border border-slate-200'
                        }`}
                      >
                        {doc.totalOcorrencias} ocorrências ({percTotal}%)
                      </span>
                    </div>
                  </div>

                  {/* Grade de Chunks do Documento */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {doc.chunks.map((chunk) => {
                      const freq = frequenciaPorChunk.get(chunk.id_chunk) || 0;
                      const isSelected = chunkInspecionado?.id_chunk === chunk.id_chunk;

                      return (
                        <button
                          key={chunk.id_chunk}
                          onClick={() => setChunkInspecionadoId(chunk.id_chunk)}
                          title={`${chunk.id_chunk} (Pág. ${chunk.paginas.join(', ')}): ${freq} ocorrência(s) de "${termoSelecionado}"`}
                          className={`w-7 h-7 sm:w-8 sm:h-8 rounded flex items-center justify-center text-[11px] font-mono border transition-all relative ${getHeatmapColor(
                            freq
                          )} ${
                            isSelected
                              ? 'ring-2 ring-sky-600 ring-offset-1 scale-110 z-10'
                              : ''
                          }`}
                        >
                          {freq > 0 ? freq : <span className="opacity-40">·</span>}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Conteúdo do Mapa: Modo Fita Panorâmica */}
        {modoVisualizacao === 'fita' && (
          <div className="space-y-2 pt-2">
            <div className="text-xs text-slate-500 flex items-center justify-between">
              <span>Sequência linear contínua (Chunks #1 ao #{todosChunks.length}):</span>
              <span className="font-mono">Clique em qualquer célula para inspecionar</span>
            </div>

            <div className="flex flex-wrap gap-1 bg-slate-50 p-3 rounded-lg border border-slate-200 max-h-64 overflow-y-auto">
              {todosChunks.map((chunk, idx) => {
                const freq = frequenciaPorChunk.get(chunk.id_chunk) || 0;
                const isSelected = chunkInspecionado?.id_chunk === chunk.id_chunk;

                return (
                  <button
                    key={chunk.id_chunk}
                    onClick={() => setChunkInspecionadoId(chunk.id_chunk)}
                    title={`#${idx + 1} - ${chunk.id_chunk} (${chunk.nome_arquivo}): ${freq}x "${termoSelecionado}"`}
                    className={`w-6 h-6 sm:w-7 sm:h-7 rounded flex items-center justify-center text-[10px] font-mono border transition-all ${getHeatmapColor(
                      freq
                    )} ${
                      isSelected
                        ? 'ring-2 ring-sky-600 ring-offset-1 scale-110 z-10'
                        : ''
                    }`}
                  >
                    {freq > 0 ? freq : ''}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Painel de Inspeção do Chunk Clicado no Mapa */}
        {chunkInspecionado && (
          <div className="bg-sky-50/50 border border-sky-200 rounded-lg p-3.5 text-xs space-y-2 animate-in fade-in duration-150">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-sky-200/80">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sky-800 bg-sky-100 border border-sky-300 px-2 py-0.5 rounded">
                  {chunkInspecionado.id_chunk}
                </span>
                <span className="font-semibold text-slate-800">
                  {chunkInspecionado.nome_arquivo}
                </span>
                <span className="text-slate-500 font-mono">
                  Página(s) [{chunkInspecionado.paginas.join(', ')}]
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="font-mono font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">
                  {frequenciaPorChunk.get(chunkInspecionado.id_chunk) || 0} ocorrência(s) de "{termoSelecionado}"
                </span>
                <button
                  onClick={() => setChunkInspecionadoId(null)}
                  className="text-slate-400 hover:text-slate-600 font-medium"
                  title="Fechar inspetor"
                >
                  ✕
                </button>
              </div>
            </div>

            <p className="text-slate-800 text-xs sm:text-sm leading-relaxed bg-white p-3 rounded-md border border-slate-200 max-h-36 overflow-y-auto">
              {highlightTermo(chunkInspecionado.texto, termoSelecionado)}
            </p>
          </div>
        )}
      </div>

      {/* Two Column Layout: Term browser and Postings viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Term search & list */}
        <div className="lg:col-span-5 bg-white border border-slate-200 p-4 rounded-xl flex flex-col space-y-3 shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Hash className="w-4 h-4 text-sky-600" />
              Vocabulário ({termosFiltrados.length})
            </h3>
            <span className="text-xs text-slate-500">Ordem lexicográfica</span>
          </div>

          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={filtroTermo}
              onChange={(e) => {
                setFiltroTermo(e.target.value);
                setPaginaTermos(1);
              }}
              placeholder="Filtrar vocabulário..."
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-1.5 max-h-[480px] overflow-y-auto pr-1">
            {termosExibidos.map((t) => {
              const info = indiceData?.indice_invertido[t];
              const isSelected = termoSelecionado === t;
              return (
                <button
                  key={t}
                  onClick={() => {
                    setTermoSelecionado(t);
                    setChunkInspecionadoId(null);
                  }}
                  className={`text-left px-2.5 py-1.5 rounded-md text-xs font-mono flex items-center justify-between transition-colors ${
                    isSelected
                      ? 'bg-sky-600 text-white font-bold shadow-2xs'
                      : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200/60'
                  }`}
                >
                  <span className="truncate mr-1">{t}</span>
                  <span className="text-[10px] opacity-75 shrink-0">
                    {info?.frequencia_total || 0}
                  </span>
                </button>
              );
            })}
          </div>

          {totalPaginas > 1 && (
            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200">
              <button
                disabled={paginaTermos <= 1}
                onClick={() => setPaginaTermos((p) => Math.max(1, p - 1))}
                className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-40 rounded"
              >
                Ant.
              </button>
              <span className="font-medium text-slate-700">
                {paginaTermos} / {totalPaginas}
              </span>
              <button
                disabled={paginaTermos >= totalPaginas}
                onClick={() => setPaginaTermos((p) => Math.min(totalPaginas, p + 1))}
                className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-40 rounded"
              >
                Próx.
              </button>
            </div>
          )}
        </div>

        {/* Postings List Detail for selected term */}
        <div className="lg:col-span-7 bg-white border border-slate-200 p-5 rounded-xl space-y-4 shadow-xs">
          <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-500">Postings do Termo:</div>
              <div className="text-xl font-bold text-sky-700 font-mono mt-0.5">
                "{termoSelecionado}"
              </div>
            </div>
            {dadosTermoSelecionado && (
              <div className="text-right text-xs">
                <span className="bg-sky-50 text-sky-700 border border-sky-200 px-2.5 py-1 rounded-md font-mono font-semibold">
                  {dadosTermoSelecionado.chunks.length} chunks • {dadosTermoSelecionado.frequencia_total} ocorrências
                </span>
              </div>
            )}
          </div>

          {dadosTermoSelecionado ? (
            <div className="space-y-3 max-h-[520px] overflow-y-auto pr-2">
              {dadosTermoSelecionado.chunks.map((posting) => {
                const chunk = chunksMap.get(posting.id_chunk);
                const isSelectedInHeatmap = chunkInspecionado?.id_chunk === posting.id_chunk;

                return (
                  <div
                    key={posting.id_chunk}
                    onClick={() => setChunkInspecionadoId(posting.id_chunk)}
                    className={`border rounded-lg p-3 text-xs space-y-2 transition-all cursor-pointer ${
                      isSelectedInHeatmap
                        ? 'bg-amber-50/70 border-amber-300 ring-1 ring-amber-400'
                        : 'bg-slate-50 border-slate-200 hover:border-slate-300 hover:bg-slate-100/60'
                    }`}
                  >
                    <div className="flex items-center justify-between text-slate-500">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-sky-700">
                          {posting.id_chunk}
                        </span>
                        {chunk && (
                          <span className="text-slate-800 font-medium truncate max-w-xs">
                            {chunk.nome_arquivo}
                          </span>
                        )}
                      </div>
                      <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-mono font-semibold">
                        freq: {posting.frequencia}
                      </span>
                    </div>

                    {chunk && (
                      <p className="text-slate-800 line-clamp-3 leading-relaxed font-sans bg-white p-2.5 rounded border border-slate-200">
                        {highlightTermo(chunk.texto, termoSelecionado)}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center py-10">
              Selecione um termo no vocabulário para inspecionar sua lista de postings invertida.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
