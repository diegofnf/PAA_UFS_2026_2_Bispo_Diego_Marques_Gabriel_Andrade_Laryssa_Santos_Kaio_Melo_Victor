import React, { useState, useMemo } from 'react';
import { Search, X, SlidersHorizontal, ArrowDownUp, Clock, FileText, CheckCircle2, Copy, Check, ExternalLink } from 'lucide-react';
import { Chunk, DocumentoCatalogo, IndiceInvertidoData, SearchResultItem, SearchMetrics } from '../types';
import { executarBuscaLexical } from '../utils/searchEngine';
import { tokenizar } from '../utils/tokenizer';

interface SearchTabProps {
  documentos: DocumentoCatalogo[];
  chunks: Chunk[];
  chunksMap: Map<string, Chunk>;
  indiceData: IndiceInvertidoData | null;
}

export const SearchTab: React.FC<SearchTabProps> = ({
  documentos,
  chunksMap,
  indiceData,
}) => {
  const [consulta, setConsulta] = useState<string>('bolsa mestrado');
  const [modo, setModo] = useState<'OU' | 'E'>('OU');
  const [metrica, setMetrica] = useState<'tf_idf' | 'frequencia'>('tf_idf');
  const [k, setK] = useState<number>(10);
  const [docFiltro, setDocFiltro] = useState<string>('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const sugestoes = [
    'bolsa mestrado',
    'credenciamento docente',
    'destinação recursos',
    'regimento interno',
    'comissão de bolsas',
    'edital capes',
    'produção intelectual',
    'qualificação de dissertação',
  ];

  const searchResult = useMemo(() => {
    if (!indiceData || !consulta.trim()) {
      return {
        resultados: [] as SearchResultItem[],
        metricas: {
          tempoBuscaMs: 0,
          tempoOrdenacaoMs: 0,
          totalComparacoesMergeSort: 0,
          candidatosEncontrados: 0,
          termosConsultados: [],
        } as SearchMetrics,
      };
    }

    return executarBuscaLexical(consulta, chunksMap, indiceData, {
      modo,
      metrica,
      k,
      idDocumentoFiltro: docFiltro || undefined,
    });
  }, [consulta, modo, metrica, k, docFiltro, chunksMap, indiceData]);

  const queryTokensSet = useMemo(() => {
    return new Set(tokenizar(consulta));
  }, [consulta]);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const highlightText = (text: string) => {
    if (queryTokensSet.size === 0) return text;

    // Divide preservando tokens e delimitadores
    const partes = text.split(/([^\W_]+)/gu);
    return partes.map((parte, index) => {
      const normalizado = parte.normalize('NFC').toLowerCase();
      if (queryTokensSet.has(normalizado)) {
        return (
          <mark
            key={index}
            className="bg-amber-100 text-amber-900 font-semibold px-1 rounded border-b border-amber-300"
          >
            {parte}
          </mark>
        );
      }
      return parte;
    });
  };

  const getDocInfo = (idDocumento: string) => {
    return documentos.find((d) => d.id_documento === idDocumento);
  };

  return (
    <div className="space-y-6">
      {/* Search Input Box */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={consulta}
            onChange={(e) => setConsulta(e.target.value)}
            placeholder="Digite termos para busca nos regulamentos (ex.: bolsas critérios mestrado, credenciamento...)"
            className="w-full pl-12 pr-10 py-3.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 text-sm md:text-base font-normal shadow-2xs"
          />
          {consulta && (
            <button
              onClick={() => setConsulta('')}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
              title="Limpar consulta"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 text-xs">
          <span className="text-slate-500 flex items-center gap-1 mr-1">
            <span>Sugestões:</span>
          </span>
          {sugestoes.map((sug) => (
            <button
              key={sug}
              onClick={() => setConsulta(sug)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                consulta.toLowerCase() === sug.toLowerCase()
                  ? 'bg-sky-50 text-sky-700 border border-sky-300 font-medium'
                  : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200'
              }`}
            >
              {sug}
            </button>
          ))}
        </div>

        {/* Search Engine Controls & Parameters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-100 text-xs">
          {/* Boolean Mode */}
          <div>
            <label className="text-slate-600 mb-1.5 font-medium flex items-center gap-1">
              <SlidersHorizontal className="w-3.5 h-3.5 text-sky-600" />
              Operador Booleano
            </label>
            <div className="grid grid-cols-2 gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button
                onClick={() => setModo('OU')}
                className={`py-1.5 text-center rounded font-medium transition-all ${
                  modo === 'OU'
                    ? 'bg-sky-600 text-white shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Recupera chunks que contenham pelo menos um dos termos"
              >
                OU (União)
              </button>
              <button
                onClick={() => setModo('E')}
                className={`py-1.5 text-center rounded font-medium transition-all ${
                  modo === 'E'
                    ? 'bg-sky-600 text-white shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Recupera apenas chunks que contenham todos os termos da consulta"
              >
                E (Interseção)
              </button>
            </div>
          </div>

          {/* Ranking Metric */}
          <div>
            <label className="text-slate-600 mb-1.5 font-medium flex items-center gap-1">
              <ArrowDownUp className="w-3.5 h-3.5 text-sky-600" />
              Métrica de Relevância
            </label>
            <div className="grid grid-cols-2 gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button
                onClick={() => setMetrica('tf_idf')}
                className={`py-1.5 text-center rounded font-medium transition-all ${
                  metrica === 'tf_idf'
                    ? 'bg-sky-600 text-white shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Ponderação TF-IDF normalizada pelo tamanho do chunk"
              >
                TF-IDF
              </button>
              <button
                onClick={() => setMetrica('frequencia')}
                className={`py-1.5 text-center rounded font-medium transition-all ${
                  metrica === 'frequencia'
                    ? 'bg-sky-600 text-white shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Soma de frequência bruta das palavras"
              >
                Frequência
              </button>
            </div>
          </div>

          {/* Top-K cut */}
          <div>
            <label className="block text-slate-600 mb-1.5 font-medium">
              Limite Top-K
            </label>
            <select
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            >
              <option value={5}>Top 5 chunks</option>
              <option value={10}>Top 10 chunks</option>
              <option value={20}>Top 20 chunks</option>
              <option value={50}>Top 50 chunks</option>
              <option value={0}>Todos os resultados</option>
            </select>
          </div>

          {/* Document Filter */}
          <div>
            <label className="block text-slate-600 mb-1.5 font-medium">
              Filtrar por Documento
            </label>
            <select
              value={docFiltro}
              onChange={(e) => setDocFiltro(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 truncate"
            >
              <option value="">Todos os 7 documentos</option>
              {documentos.map((doc) => (
                <option key={doc.id_documento} value={doc.id_documento}>
                  {doc.id_documento} - {doc.nome_arquivo}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Algorithmic & Performance Execution Metrics (PAA Scope) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-slate-500 text-xs flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-sky-600" />
            <span>Tempo Índice / Busca</span>
          </div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {searchResult.metricas.tempoBuscaMs.toFixed(2)}{' '}
            <span className="text-xs font-normal text-slate-500">ms</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">Consulta O(1) por termo</p>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-slate-500 text-xs flex items-center gap-1.5">
            <ArrowDownUp className="w-3.5 h-3.5 text-amber-600" />
            <span>Tempo Merge Sort</span>
          </div>
          <div className="text-lg font-bold text-slate-900 mt-1">
            {searchResult.metricas.tempoOrdenacaoMs.toFixed(2)}{' '}
            <span className="text-xs font-normal text-slate-500">ms</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">Algoritmo O(n log n)</p>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-slate-500 text-xs">Comparações no Merge Sort</div>
          <div className="text-lg font-bold text-sky-700 mt-1">
            {searchResult.metricas.totalComparacoesMergeSort.toLocaleString('pt-BR')}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {searchResult.metricas.candidatosEncontrados > 1
              ? `n = ${searchResult.metricas.candidatosEncontrados} candidatos`
              : 'Sem ordenação necessária'}
          </p>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-slate-500 text-xs">Candidatos / Retornados</div>
          <div className="text-lg font-bold text-emerald-600 mt-1">
            {searchResult.resultados.length}{' '}
            <span className="text-xs font-normal text-slate-500">
              de {searchResult.metricas.candidatosEncontrados}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {k > 0 ? `Top-${k} ativado` : 'Sem limite (todos)'}
          </p>
        </div>
      </div>

      {/* Query Terms Breakdown */}
      {searchResult.metricas.termosConsultados.length > 0 && indiceData && (
        <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-600 font-medium">Termos no Vocabulário:</span>
          {searchResult.metricas.termosConsultados.map((termo) => {
            const info = indiceData.indice_invertido[termo];
            const presente = !!info;
            return (
              <span
                key={termo}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
                  presente
                    ? 'bg-sky-50 text-sky-800 border-sky-200'
                    : 'bg-rose-50 text-rose-800 border-rose-200'
                }`}
              >
                <span className="font-semibold">{termo}</span>
                {presente ? (
                  <span className="text-[10px] text-sky-700 bg-sky-100/70 px-1.5 py-0.2 rounded">
                    {info.chunks.length} chunks ({info.frequencia_total}x)
                  </span>
                ) : (
                  <span className="text-[10px] text-rose-600">não no índice</span>
                )}
              </span>
            );
          })}
        </div>
      )}

      {/* Results Header */}
      <div className="flex items-center justify-between pt-2">
        <h3 className="text-sm font-semibold text-slate-800">
          Resultados Ordenados ({searchResult.resultados.length})
        </h3>
        <span className="text-xs text-slate-500">
          Ordenação estável por Merge Sort
        </span>
      </div>

      {/* Results List */}
      {searchResult.resultados.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-10 text-center text-slate-500 shadow-xs">
          <Search className="w-10 h-10 mx-auto text-slate-400 mb-3" />
          <p className="font-medium text-slate-800">Nenhum chunk correspondente encontrado</p>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            {modo === 'E'
              ? 'O modo "E (Interseção)" exige que todos os termos estejam presentes no mesmo chunk. Tente alternar para o modo "OU (União)".'
              : 'Verifique a ortografia dos termos ou tente palavras-chave mais genéricas presentes nos regulamentos.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {searchResult.resultados.map((item, idx) => {
            const chunk = item.chunk;
            const doc = getDocInfo(chunk.id_documento);
            const isExpanded = expandedId === chunk.id_chunk;
            const cruzouPagina = chunk.paginas.length > 1;

            return (
              <div
                key={chunk.id_chunk}
                className="bg-white border border-slate-200 hover:border-sky-300 rounded-xl p-5 transition-all shadow-xs"
              >
                {/* Header row */}
                <div className="flex flex-wrap items-start justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="bg-sky-50 text-sky-700 border border-sky-200 text-xs px-2.5 py-0.5 rounded-full font-mono font-bold">
                      #{idx + 1} • {chunk.id_chunk}
                    </span>

                    <span className="text-xs text-slate-800 font-medium flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5 text-sky-600" />
                      {chunk.nome_arquivo}
                    </span>

                    {cruzouPagina ? (
                      <span className="bg-amber-50 text-amber-800 border border-amber-200 text-[11px] px-2 py-0.5 rounded-full font-medium">
                        Páginas [{chunk.paginas.join(', ')}] • Cruzou Página
                      </span>
                    ) : (
                      <span className="bg-slate-100 text-slate-700 border border-slate-200 text-[11px] px-2 py-0.5 rounded-full font-medium">
                        Página {chunk.paginas[0]}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs px-2.5 py-1 rounded-lg font-mono font-semibold">
                      Score: {item.score}
                    </div>

                    <button
                      onClick={() => copyToClipboard(chunk.texto, chunk.id_chunk)}
                      className="p-1.5 text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors"
                      title="Copiar texto do chunk"
                    >
                      {copiedId === chunk.id_chunk ? (
                        <Check className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>

                    {doc?.fonte_url && (
                      <a
                        href={doc.fonte_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 text-slate-500 hover:text-sky-600 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors"
                        title="Ver documento oficial no SIGAA"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>

                {/* Term frequencies breakdown in this chunk */}
                <div className="flex flex-wrap items-center gap-1.5 my-2.5 text-[11px]">
                  <span className="text-slate-500">Termos encontrados:</span>
                  {item.termosEncontrados.map((t) => (
                    <span
                      key={t.termo}
                      className="bg-sky-50 text-sky-800 px-2 py-0.5 rounded border border-sky-200 font-mono"
                    >
                      {t.termo} ({t.frequencia}x)
                    </span>
                  ))}
                  <span className="text-slate-500 ml-auto font-mono text-[10px]">
                    Palavras: {chunk.quantidade_palavras} (pos. {chunk.inicio_palavra}..{chunk.fim_palavra})
                  </span>
                </div>

                {/* Chunk Text */}
                <div className="text-slate-800 text-sm leading-relaxed bg-slate-50/70 p-3.5 rounded-lg border border-slate-200 font-sans">
                  {isExpanded ? (
                    <p className="whitespace-pre-wrap">{highlightText(chunk.texto)}</p>
                  ) : (
                    <p className="line-clamp-4">
                      {highlightText(chunk.texto)}
                    </p>
                  )}
                </div>

                {/* Footer / Expand Button */}
                <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : chunk.id_chunk)}
                    className="text-sky-700 hover:text-sky-800 font-semibold transition-colors"
                  >
                    {isExpanded ? 'Recolher texto' : 'Exibir texto completo do chunk'}
                  </button>
                  <span className="text-[11px] text-slate-500">
                    Chunk {chunk.ordem_chunk_documento} do documento
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
