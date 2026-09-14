import React from 'react';
import { Search, FileText, Layers, Hash, GitBranch, ExternalLink } from 'lucide-react';

interface NavbarProps {
  activeTab: 'search' | 'corpus' | 'chunks' | 'index' | 'pipeline';
  setActiveTab: (tab: 'search' | 'corpus' | 'chunks' | 'index' | 'pipeline') => void;
  totalDocs: number;
  totalChunks: number;
  totalTermos: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  totalDocs,
  totalChunks,
  totalTermos,
}) => {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between py-3 gap-3">
          {/* Logo & Info */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-blue-700 flex items-center justify-center shadow-md shadow-sky-500/15 text-white font-bold text-lg">
              UFS
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-slate-900 tracking-tight">
                  Regulamentos Acadêmicos PROCC/UFS
                </h1>
                <span className="bg-sky-50 text-sky-700 border border-sky-200 text-xs px-2 py-0.5 rounded-full font-medium">
                  PAA 2026.2
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Recuperação Lexical, Índice Invertido e Ordenação Merge Sort
              </p>
            </div>
          </div>

          {/* Quick Metrics & Links */}
          <div className="flex items-center gap-2 sm:gap-3 text-xs">
            <div className="hidden sm:flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-slate-600">
              <span className="text-sky-700 font-semibold">{totalDocs}</span> docs
              <span className="text-slate-300">•</span>
              <span className="text-sky-700 font-semibold">{totalChunks}</span> chunks
              <span className="text-slate-300">•</span>
              <span className="text-sky-700 font-semibold">{totalTermos.toLocaleString('pt-BR')}</span> termos
            </div>

            <a
              href="https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Farias_Franzone_Melo_Victor/blob/main/orquestrador_pipeline.ipynb"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 px-2.5 py-1.5 rounded-lg transition-colors font-medium shadow-2xs"
              title="Abrir no Google Colab"
            >
              <span>Colab</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Tab Navigation: Pipeline & Relatórios -> Corpus -> Chunks -> Índice invertido -> Busca Lexical & Top K */}
        <nav className="flex space-x-1 sm:space-x-2 border-t border-slate-200/90 pt-1 overflow-x-auto no-scrollbar">
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'pipeline'
                ? 'border-sky-600 text-sky-700 bg-sky-50/70 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            <GitBranch className="w-4 h-4" />
            Pipeline & Relatórios
          </button>

          <button
            onClick={() => setActiveTab('corpus')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'corpus'
                ? 'border-sky-600 text-sky-700 bg-sky-50/70 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            <FileText className="w-4 h-4" />
            Corpus (7 Documentos)
          </button>

          <button
            onClick={() => setActiveTab('chunks')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'chunks'
                ? 'border-sky-600 text-sky-700 bg-sky-50/70 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            <Layers className="w-4 h-4" />
            Chunks (182)
          </button>

          <button
            onClick={() => setActiveTab('index')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'index'
                ? 'border-sky-600 text-sky-700 bg-sky-50/70 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            <Hash className="w-4 h-4" />
            Índice Invertido
          </button>

          <button
            onClick={() => setActiveTab('search')}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
              activeTab === 'search'
                ? 'border-sky-600 text-sky-700 bg-sky-50/70 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            <Search className="w-4 h-4" />
            Busca Lexical & Top-K
          </button>
        </nav>
      </div>
    </header>
  );
};
