/**
 * Implementação do algoritmo de ordenação por intercalação (Merge Sort)
 * em conformidade com o escopo da disciplina PAA (Projeto e Análise de Algoritmos - UFS).
 * Complexidade de tempo: O(n log n) no pior, melhor e médio caso.
 * Complexidade de espaço: O(n).
 * Registra o número de comparações realizadas para fins de análise empírica.
 */
export interface MergeSortResult<T> {
  sorted: T[];
  comparacoes: number;
  tempoMs: number;
}

/**
 * Comparador que separa a chave primária (score) da chave de desempate
 * (id_chunk), para que o número de comparações conte exatamente como em
 * `1_scripts/4_buscar_e_ordenar.py` (Etapa 4): uma comparação de score e,
 * apenas em caso de empate, uma segunda comparação de id_chunk.
 */
export interface ComparadorComDesempate<T> {
  /** Devolve <0, 0 ou >0. Zero indica empate na chave primária. */
  compararScore(a: T, b: T): number;
  /** Desempate por chave secundária; chamado somente quando compararScore devolve 0. */
  desempatar(a: T, b: T): number;
}

export function mergeSort<T>(
  array: T[],
  comparador: ComparadorComDesempate<T>
): MergeSortResult<T> {
  const tInicio = performance.now();
  let comparacoes = 0;

  function merge(esquerda: T[], direita: T[]): T[] {
    const resultado: T[] = [];
    let i = 0;
    let j = 0;

    while (i < esquerda.length && j < direita.length) {
      comparacoes++;
      const cmp = comparador.compararScore(esquerda[i], direita[j]);
      if (cmp < 0) {
        resultado.push(esquerda[i]);
        i++;
      } else if (cmp > 0) {
        resultado.push(direita[j]);
        j++;
      } else {
        comparacoes++;
        if (comparador.desempatar(esquerda[i], direita[j]) <= 0) {
          resultado.push(esquerda[i]);
          i++;
        } else {
          resultado.push(direita[j]);
          j++;
        }
      }
    }

    while (i < esquerda.length) {
      resultado.push(esquerda[i]);
      i++;
    }

    while (j < direita.length) {
      resultado.push(direita[j]);
      j++;
    }

    return resultado;
  }

  function sort(lista: T[]): T[] {
    if (lista.length <= 1) {
      return lista;
    }
    const meio = Math.floor(lista.length / 2);
    const esquerda = sort(lista.slice(0, meio));
    const direita = sort(lista.slice(meio));
    return merge(esquerda, direita);
  }

  const sorted = sort([...array]);
  const tempoMs = performance.now() - tInicio;

  return {
    sorted,
    comparacoes,
    tempoMs: Number(tempoMs.toFixed(3)),
  };
}
