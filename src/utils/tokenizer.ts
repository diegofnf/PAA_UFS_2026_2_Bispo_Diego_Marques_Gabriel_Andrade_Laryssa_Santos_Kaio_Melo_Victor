/**
 * Tokenizador que preserva paridade estrita com o script Python 3_construir_indice_invertido.py
 * Regras:
 * - Normalização Unicode NFC
 * - Casefold (lowercase)
 * - Extração de tokens alfanuméricos preservando acentuação [^\W_]+
 */
export function tokenizar(texto: string): string[] {
  if (!texto) return [];
  const normalizado = texto.normalize('NFC').toLowerCase();
  const tokens = normalizado.match(/[^\W_]+/gu);
  return tokens || [];
}
