/**
 * Tokenizador que preserva paridade estrita com o script Python 3_construir_indice_invertido.py
 * Regras:
 * - Normalização Unicode NFC
 * - Casefold (lowercase)
 * - Extração de tokens alfanuméricos preservando acentuação
 *
 * Nota: em JavaScript `\w` é ASCII-only por especificação, mesmo com a flag `u`
 * (`/[^\W_]+/u` ainda separa "critérios" em "crit" + "rios"). Por isso usamos a
 * propriedade Unicode `\p{L}\p{N}`, com a flag `u`, para reproduzir exatamente o
 * comportamento de `\w` do Python, que é Unicode-aware.
 */
const PADRAO_TOKEN = /[\p{L}\p{N}]+/gu;

export function tokenizar(texto: string): string[] {
  if (!texto) return [];
  const normalizado = texto.normalize('NFC').toLowerCase();
  const tokens = normalizado.match(PADRAO_TOKEN);
  return tokens || [];
}
