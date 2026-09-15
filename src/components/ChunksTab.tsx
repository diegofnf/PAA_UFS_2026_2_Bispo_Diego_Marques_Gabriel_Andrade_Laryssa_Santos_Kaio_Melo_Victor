import React, { useState, useMemo } from 'react';
import { Layers, Search, Filter, Copy, Check, FileText, CheckCircle2 } from 'lucide-react';
import { Chunk, DocumentoCatalogo } from '../types';

interface ChunksTabProps {
  chunks: Chunk[];
  documentos: DocumentoCatalogo[];
}

export const ChunksTab: React.FC<ChunksTabProps> = ({ chunks, documentos }) => {
  const [buscaTexto, setBuscaTexto] = useState('');
  const [filtroDoc, setFiltroDoc] = useState('');
  const [apenasCruzamPagina, setApenasCruzamPagina] = useState(false);
  const [copiadoId, setCopiadoId] = useState<string | null>(null);
  const [paginaAtual, setPaginaAtual] = useState(1);
  const itensPorPagina = 15;

  const totalCruzam = useMemo(() => {
    return chunks.filter((c) => c.paginas.length > 1).length;
  }, [chunks]);

  const chunksFiltrados = useMemo(() => {
    return chunks.filter((c) => {
      if (filtroDoc && c.id_documento !== filtroDoc) return false;
      if (apenasCruzamPagina && c.paginas.length <= 1) return false;
      if (buscaTexto.trim()) {
        const termo = buscaTexto.toLowerCase();
        return (
          c.id_chunk.toLowerCase().includes(termo) ||
          c.texto.toLowerCase().includes(termo) ||
          c.nome_arquivo.toLowerCase().includes(termo)
        );
      }
      return true;
    });
  }, [chunks, filtroDoc, apenasCruzamPagina, buscaTexto]);

  const totalPaginas = Math.ceil(chunksFiltrados.length / itensPorPagina) || 1;
  const chunksExibidos = useMemo(() => {
    const inicio = (paginaAtual - 1) * itensPorPagina;
    return chunksFiltrados.slice(inicio, inicio + itensPorPagina);
  }, [chunksFiltrados, paginaAtual]);

  const copyChunk = (texto: string, id: string) => {
    navigator.clipboard.writeText(texto);
    setCopiadoId(id);
    setTimeout(() => setCopiadoId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Chunking Metrics Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Total de Chunks</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{chunks.length}</div>
          <span className="text-[11px] text-sky-700 font-medium">Coleção contínua gerada</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Configuração de Janelamento</span>
          <div className="text-xl font-bold text-slate-900 mt-1">200 / 30</div>
          <span className="text-[11px] text-slate-500">200 palavras • 30 overlap (passo 170)</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Overlap Entre Páginas</span>
          <div className="text-2xl font-bold text-amber-600 mt-1">{totalCruzam}</div>
          <span className="text-[11px] text-amber-700 font-medium">
            {((totalCruzam / chunks.length) * 100).toFixed(1)}% cruzam fronteiras
          </span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Densidade Média</span>
          <div className="text-2xl font-bold text-emerald-600 mt-1">196.8</div>
          <span className="text-[11px] text-slate-500">palavras/chunk (alta densidade)</span>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white border border-slate-200 p-4 rounded-xl space-y-3 shadow-xs">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={buscaTexto}
              onChange={(e) => {
                setBuscaTexto(e.target.value);
                setPaginaAtual(1);
              }}
              placeholder="Buscar em texto ou ID de chunk..."
              className="w-full pl-9 pr-3 py-2 bg-white border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>

          {/* Doc filter */}
          <div>
            <select
              value={filtroDoc}
              onChange={(e) => {
                setFiltroDoc(e.target.value);
                setPaginaAtual(1);
              }}
              className="w-full py-2 px-3 bg-white border border-slate-300 rounded-lg text-xs sm:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            >
              <option value="">Todos os 7 documentos</option>
              {documentos.map((doc) => (
                <option key={doc.id_documento} value={doc.id_documento}>
                  {doc.id_documento} - {doc.nome_arquivo}
                </option>
              ))}
            </select>
          </div>

          {/* Toggle cross-page */}
          <label className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-2 rounded-lg cursor-pointer text-xs text-slate-700 hover:border-slate-300 select-none">
            <input
              type="checkbox"
              checked={apenasCruzamPagina}
              onChange={(e) => {
                setApenasCruzamPagina(e.target.checked);
                setPaginaAtual(1);
              }}
              className="rounded bg-white border-slate-300 text-sky-600 focus:ring-sky-500 h-4 w-4"
            />
            <span>Apenas chunks que cruzam páginas ({totalCruzam})</span>
          </label>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <span>Exibindo {chunksFiltrados.length} de {chunks.length} chunks</span>
          {chunksFiltrados.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                disabled={paginaAtual <= 1}
                onClick={() => setPaginaAtual((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-40 rounded transition-colors"
              >
                Anterior
              </button>
              <span className="font-medium text-slate-700">
                Página {paginaAtual} de {totalPaginas}
              </span>
              <button
                disabled={paginaAtual >= totalPaginas}
                onClick={() => setPaginaAtual((p) => Math.min(totalPaginas, p + 1))}
                className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 disabled:opacity-40 rounded transition-colors"
              >
                Próxima
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Chunks List */}
      <div className="space-y-3">
        {chunksExibidos.map((chunk) => {
          const cruzou = chunk.paginas.length > 1;
          return (
            <div
              key={chunk.id_chunk}
              className="bg-white border border-slate-200 hover:border-sky-300 rounded-xl p-4 transition-all shadow-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-100 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono font-bold text-sky-700 bg-sky-50 border border-sky-200 px-2 py-0.5 rounded">
                    {chunk.id_chunk}
                  </span>
                  <span className="text-slate-800 font-medium flex items-center gap-1">
                    <FileText className="w-3.5 h-3.5 text-slate-400" />
                    {chunk.nome_arquivo}
                  </span>
                  {cruzou ? (
                    <span className="bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded text-[11px] font-medium">
                      Páginas [{chunk.paginas.join(', ')}] • Cruzou Página
                    </span>
                  ) : (
                    <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded text-[11px]">
                      Página {chunk.paginas[0]}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 text-slate-500 text-xs">
                  <span className="font-mono text-[11px]">
                    Palavras: {chunk.quantidade_palavras} (pos. {chunk.inicio_palavra}..{chunk.fim_palavra})
                  </span>
                  <button
                    onClick={() => copyChunk(chunk.texto, chunk.id_chunk)}
                    className="p-1 hover:text-slate-900 text-slate-500 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded transition-colors"
                    title="Copiar texto do chunk"
                  >
                    {copiadoId === chunk.id_chunk ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <p className="mt-3 text-xs sm:text-sm text-slate-800 leading-relaxed font-sans bg-slate-50/70 p-3.5 rounded-lg border border-slate-200/80">
                {chunk.texto}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
