"""Constrói o índice invertido dos chunks normalizados."""

import argparse
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


PADRAO_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def tokenizar(texto):
    """Gera tokens alfanuméricos, preservando acentos e sem stopwords."""
    texto = unicodedata.normalize("NFC", texto).casefold()
    return PADRAO_TOKEN.findall(texto)


def construir_indice(chunks):
    """Mapeia cada termo para chunks e frequências de ocorrência."""
    ocorrencias = defaultdict(Counter)

    for chunk in chunks:
        id_chunk = chunk["id_chunk"]
        for termo in tokenizar(chunk.get("texto", "")):
            ocorrencias[termo][id_chunk] += 1

    indice = {}
    for termo in sorted(ocorrencias):
        contagens = ocorrencias[termo]
        indice[termo] = {
            "chunks": [
                {"id_chunk": id_chunk, "frequencia": contagens[id_chunk]}
                for id_chunk in sorted(contagens)
            ],
            "frequencia_total": sum(contagens.values()),
        }
    return indice


def salvar(caminho, dados):
    """Grava um artefato JSON UTF-8."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    """Executa a Etapa 3 — Indexação e índice invertido."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entrada",
        type=Path,
        default=Path("4_chunks/chunks.json"),
        help="Arquivo JSON com os chunks de entrada.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("5_indexacao/indice_invertido.json"),
        help="Arquivo JSON de saída do índice invertido.",
    )
    parser.add_argument(
        "--relatorio",
        type=Path,
        default=Path("5_indexacao/relatorio_indexacao.json"),
        help="Arquivo JSON com as estatísticas da indexação.",
    )
    args = parser.parse_args()

    if not args.entrada.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {args.entrada}")

    dados = json.loads(args.entrada.read_text(encoding="utf-8"))
    chunks = dados.get("chunks", [])
    if not chunks:
        raise ValueError("Nenhum chunk encontrado no arquivo de entrada.")

    inicio = time.perf_counter()
    indice = construir_indice(chunks)
    tempo = round(time.perf_counter() - inicio, 6)
    total_postings = sum(len(registro["chunks"]) for registro in indice.values())
    total_ocorrencias = sum(registro["frequencia_total"] for registro in indice.values())

    metadados = {
        "estrategia": "termo_para_ids_de_chunks",
        "regras_tokenizacao": [
            "Unicode NFC",
            "casefold para comparação sem distinção de caixa",
            "tokens alfanuméricos com acentos preservados",
            "sem stemming",
            "sem remoção de stopwords",
        ],
        "total_chunks_entrada": len(chunks),
        "total_termos": len(indice),
        "total_postings": total_postings,
        "total_ocorrencias": total_ocorrencias,
        "tempo_construcao_segundos": tempo,
    }
    saida = {"metadados": metadados, "indice_invertido": indice}
    relatorio = {
        "status_etapa": "concluido",
        **metadados,
        "entrada": str(args.entrada),
        "saida": str(args.saida),
    }

    salvar(args.saida, saida)
    salvar(args.relatorio, relatorio)

    ids_chunks = {chunk["id_chunk"] for chunk in chunks}
    assert all(
        item["id_chunk"] in ids_chunks
        for registro in indice.values()
        for item in registro["chunks"]
    ), "O índice não pode referenciar chunks inexistentes."
    assert len(indice) > 0, "O índice deve conter ao menos um termo."

    print(
        f"Etapa 3 concluída: {len(indice)} termos, {total_postings} postings e "
        f"{len(chunks)} chunks indexados em {tempo:.4f}s."
    )
    print(f"Artefatos salvos em: {args.saida} e {args.relatorio}")


if __name__ == "__main__":
    main()
