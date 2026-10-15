import React, { useState } from 'react';
import { FileText, ExternalLink, Hash, CheckCircle, Copy, Check, Eye, X, BookOpen } from 'lucide-react';
import { DocumentoCatalogo, DocumentoNormalizado } from '../types';

interface CorpusTabProps {
  documentos: DocumentoCatalogo[];
  documentosNormalizados: DocumentoNormalizado[];
}

export const CorpusTab: React.FC<CorpusTabProps> = ({
  documentos,
  documentosNormalizados,
}) => {
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);

  const copyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const selectedDocNorm = documentosNormalizados.find((d) => d.id_documento === selectedDocId);
  const selectedDocMeta = documentos.find((d) => d.id_documento === selectedDocId);

  const selectedPage = selectedDocNorm?.paginas.find((p) => p.numero_pagina === selectedPageNum);

  const totalBytes = documentos.reduce((acc, d) => acc + d.tamanho_bytes, 0);
  const totalPaginas = documentos.reduce((acc, d) => acc + d.quantidade_paginas, 0);

  return (
    <div className="space-y-6">
      {/* Corpus Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Total de Documentos</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{documentos.length}</div>
          <span className="text-[11px] text-sky-700 font-medium">Regulamentos PROCC/UFS</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Total de Páginas</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{totalPaginas}</div>
          <span className="text-[11px] text-emerald-700 font-medium">100% extraídas via PyMuPDF</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Volume em Disco</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            {(totalBytes / (1024 * 1024)).toFixed(2)}{' '}
            <span className="text-sm font-normal text-slate-500">MB</span>
          </div>
          <span className="text-[11px] text-slate-500">Formato original PDF</span>
        </div>

        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium">Status do Processamento</span>
          <div className="text-2xl font-bold text-emerald-600 mt-1 flex items-center gap-1.5">
            <CheckCircle className="w-5 h-5" />
            Concluído
          </div>
          <span className="text-[11px] text-slate-500">Normalização Unicode NFC</span>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="p-4 sm:p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Catálogo de Regulamentos Oficiais</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Documentos normativos da pós-graduação PROCC e Resoluções CONEPE da UFS
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 text-xs font-semibold">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Nome do Arquivo</th>
                <th className="py-3 px-4">Páginas</th>
                <th className="py-3 px-4">Tamanho</th>
                <th className="py-3 px-4">SHA-256</th>
                <th className="py-3 px-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documentos.map((doc) => (
                <tr key={doc.id_documento} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-sky-700">
                    {doc.id_documento}
                  </td>
                  <td className="py-3.5 px-4 font-medium text-slate-900">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="truncate max-w-xs sm:max-w-md" title={doc.nome_arquivo}>
                        {doc.nome_arquivo}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-700">
                    <span className="bg-slate-100 border border-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono text-xs">
                      {doc.quantidade_paginas} págs
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono">
                    {(doc.tamanho_bytes / 1024).toFixed(1)} KB
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono text-xs">
                    <div className="flex items-center gap-1.5">
                      <span>{doc.hash_sha256.substring(0, 8)}...</span>
                      <button
                        onClick={() => copyHash(doc.hash_sha256)}
                        className="text-slate-400 hover:text-slate-700 transition-colors"
                        title="Copiar Hash SHA-256 completo"
                      >
                        {copiedHash === doc.hash_sha256 ? (
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          setSelectedDocId(doc.id_documento);
                          setSelectedPageNum(1);
                        }}
                        className="inline-flex items-center gap-1 bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Ver Páginas</span>
                      </button>

                      {doc.fonte_url && (
                        <a
                          href={doc.fonte_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors"
                          title="Acessar documento no SIGAA / UFS"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">SIGAA</span>
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Page Inspector Modal */}
      {selectedDocId && selectedDocNorm && selectedDocMeta && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-sky-600" />
                <div>
                  <h4 className="text-sm sm:text-base font-semibold text-slate-900">
                    {selectedDocMeta.nome_arquivo}
                  </h4>
                  <p className="text-xs text-slate-500">
                    {selectedDocMeta.id_documento} • {selectedDocNorm.paginas.length} páginas normalizadas
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedDocId(null)}
                className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-200/60 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Page Selector Bar */}
            <div className="px-4 py-2 bg-slate-100/70 border-b border-slate-200 flex items-center gap-2 overflow-x-auto text-xs">
              <span className="text-slate-600 shrink-0 font-medium">Páginas:</span>
              <div className="flex gap-1">
                {selectedDocNorm.paginas.map((pag) => (
                  <button
                    key={pag.numero_pagina}
                    onClick={() => setSelectedPageNum(pag.numero_pagina)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      selectedPageNum === pag.numero_pagina
                        ? 'bg-sky-600 text-white font-bold shadow-2xs'
                        : 'bg-white hover:bg-slate-200 text-slate-700 border border-slate-200'
                    }`}
                  >
                    {pag.numero_pagina}
                  </button>
                ))}
              </div>
            </div>

            {/* Modal Body: Text of selected page */}
            <div className="p-5 overflow-y-auto flex-1 font-mono text-xs sm:text-sm leading-relaxed text-slate-800 bg-slate-50/50">
              {selectedPage ? (
                <div>
                  <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200 text-xs text-slate-500">
                    <span>
                      Página {selectedPage.numero_pagina} de {selectedDocNorm.paginas.length}
                    </span>
                    <span className="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200 font-sans font-medium">
                      Status: {selectedPage.status_normalizacao}
                    </span>
                  </div>
                  {selectedPage.texto_normalizado ? (
                    <pre className="whitespace-pre-wrap font-sans text-sm text-slate-800 leading-relaxed bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
                      {selectedPage.texto_normalizado}
                    </pre>
                  ) : (
                    <div className="text-center py-10 text-slate-500 font-sans">
                      (Página vazia ou sem camada de texto detectada)
                    </div>
                  )}
                </div>
              ) : (
                <p>Selecione uma página para visualizar.</p>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <span>Texto limpo e padronizado em Unicode NFC</span>
              <button
                onClick={() => setSelectedDocId(null)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white rounded-lg transition-colors font-medium"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
