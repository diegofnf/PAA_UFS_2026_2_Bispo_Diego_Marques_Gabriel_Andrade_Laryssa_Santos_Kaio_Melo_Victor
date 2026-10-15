/**
 * Stopwords em português do NLTK, normalizadas com Unicode NFC + casefold.
 *
 * Esta lista foi extraída programaticamente de `nltk.corpus.stopwords.words("portuguese")`
 * (207 palavras) para que a aplicação web reproduza exatamente o filtro aplicado por
 * `1_scripts/4_buscar_e_ordenar.py`, sem depender do runtime Python no navegador.
 */
export const STOPWORDS_PT: ReadonlySet<string> = new Set([
  'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'até',
  'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'depois',
  'do', 'dos', 'e', 'ela', 'elas', 'ele', 'eles', 'em', 'entre', 'era',
  'eram', 'essa', 'essas', 'esse', 'esses', 'esta', 'estamos', 'estar', 'estas', 'estava',
  'estavam', 'este', 'esteja', 'estejam', 'estejamos', 'estes', 'esteve', 'estive', 'estivemos', 'estiver',
  'estivera', 'estiveram', 'estiverem', 'estivermos', 'estivesse', 'estivessem', 'estivéramos', 'estivéssemos', 'estou', 'está',
  'estávamos', 'estão', 'eu', 'foi', 'fomos', 'for', 'fora', 'foram', 'forem', 'formos',
  'fosse', 'fossem', 'fui', 'fôramos', 'fôssemos', 'haja', 'hajam', 'hajamos', 'havemos', 'haver',
  'hei', 'houve', 'houvemos', 'houver', 'houvera', 'houveram', 'houverei', 'houverem', 'houveremos', 'houveria',
  'houveriam', 'houvermos', 'houverá', 'houverão', 'houveríamos', 'houvesse', 'houvessem', 'houvéramos', 'houvéssemos', 'há',
  'hão', 'isso', 'isto', 'já', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo',
  'meu', 'meus', 'minha', 'minhas', 'muito', 'na', 'nas', 'nem', 'no', 'nos',
  'nossa', 'nossas', 'nosso', 'nossos', 'num', 'numa', 'não', 'nós', 'o', 'os',
  'ou', 'para', 'pela', 'pelas', 'pelo', 'pelos', 'por', 'qual', 'quando', 'que',
  'quem', 'se', 'seja', 'sejam', 'sejamos', 'sem', 'ser', 'serei', 'seremos', 'seria',
  'seriam', 'será', 'serão', 'seríamos', 'seu', 'seus', 'somos', 'sou', 'sua', 'suas',
  'são', 'só', 'também', 'te', 'tem', 'temos', 'tenha', 'tenham', 'tenhamos', 'tenho',
  'terei', 'teremos', 'teria', 'teriam', 'terá', 'terão', 'teríamos', 'teu', 'teus', 'teve',
  'tinha', 'tinham', 'tive', 'tivemos', 'tiver', 'tivera', 'tiveram', 'tiverem', 'tivermos', 'tivesse',
  'tivessem', 'tivéramos', 'tivéssemos', 'tu', 'tua', 'tuas', 'tém', 'tínhamos', 'um', 'uma',
  'você', 'vocês', 'vos', 'à', 'às', 'é', 'éramos',
]);

/** Remove stopwords e deduplica preservando a ordem de primeira ocorrência. */
export function filtrarStopwords(tokens: string[]): { termosDistintos: string[]; removidas: string[] } {
  const removidas: string[] = [];
  const vistos = new Set<string>();
  const termosDistintos: string[] = [];

  for (const token of tokens) {
    if (STOPWORDS_PT.has(token)) {
      removidas.push(token);
    } else if (!vistos.has(token)) {
      vistos.add(token);
      termosDistintos.push(token);
    }
  }

  return { termosDistintos, removidas };
}
