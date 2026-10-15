"""Inventaria, extrai e normaliza os PDFs do corpus."""

import argparse
import hashlib
import json
import re
import time
import unicodedata
from pathlib import Path

import pymupdf


FONTES = {
    "IN_01_2026_PROCC_Credenciamento_Recredenciamento_Vagas.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=5025297&key=2d84693e082547f2c3b9e5a7211baf63",
    "IN_02_2026_PROCC_Destinacao_Recursos.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=5040212&key=bd7f4126e48c0ff0c3f3ecd020bea2af",
    "Edital_CAPES_14_2023_PRAPG.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4214078&key=9a30771aef926507ec26e66ff5da6260",
    "IN_01_2023_PROCC_Estrutura_Curricular_Mestrado.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4024039&key=3935a3b7b0d57462398d13c8fa68def5",
    "IN_01_2024_PROCC_Criterios_Bolsas.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4357246&key=807372ebd6adf4d3ad63cd51277fec38",
    "Resolucao_29_2022_CONEPE_Regimento_Interno_PROCC.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4218408&key=0f7e24ac2195143e5735697d19cb43ac",
    "Resolucao_04_2021_CONEPE_Normas_Academicas_Pos_Graduacao.pdf": "https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=2737960&key=1861aeae080b4f6318206935e3b17414",
}


def sha256(caminho):
    """Calcula a impressão digital do arquivo para identificação."""
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def motivo_pagina_vazia(pagina):
    """Classifica por que uma página não apresentou texto extraível."""
    if pagina.get_images(full=True):
        return "imagem_presente_sem_camada_textual"
    return "sem_texto_e_sem_imagem_detectavel"


def extrair_documento(caminho, document_id):
    """Extrai o texto página a página e registra o status da extração."""
    leitor = pymupdf.open(str(caminho))
    paginas = []
    for numero, pagina in enumerate(leitor, start=1):
        texto = pagina.get_text("text") or ""
        texto_limpo = texto.strip()
        registro = {
            "numero_pagina": numero,
            "texto_original": texto,
            "quantidade_caracteres": len(texto),
            "quantidade_palavras": len(texto.split()),
        }
        if texto_limpo:
            registro["status_extracao"] = "extraido"
        else:
            registro["status_extracao"] = "vazia"
            registro["motivo_status"] = motivo_pagina_vazia(pagina)
        paginas.append(registro)
    return {"id_documento": document_id, "paginas": paginas}


def normalizar_texto(texto):
    """Padroniza Unicode, quebras, espaços e hifenização do texto."""
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace("\u200b", " ")
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"(?<=\w)-\n(?=\w)", "", texto)
    texto = "\n".join(re.sub(r"[ \t]+", " ", linha).strip() for linha in texto.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def construir_saida(corpus):
    """Processa o corpus e monta catálogo, textos e avisos do pipeline."""
    catalogo = []
    extraidos = []
    normalizados = []
    avisos = []
    total_paginas = 0
    for indice, caminho in enumerate(sorted(corpus.glob("*.pdf")), start=1):
        document_id = f"doc_{indice:03d}"
        extraido = extrair_documento(caminho, document_id)
        paginas_normalizadas = []
        vazias = []
        for pagina in extraido["paginas"]:
            normalizada = {
                "numero_pagina": pagina["numero_pagina"],
                "texto_normalizado": normalizar_texto(pagina["texto_original"]),
                "status_normalizacao": "processado",
            }
            if pagina["status_extracao"] == "vazia":
                vazias.append({"numero_pagina": pagina["numero_pagina"], "motivo_status": pagina["motivo_status"]})
                normalizada["status_normalizacao"] = "vazia_preservada"
                normalizada["motivo_status"] = pagina["motivo_status"]
            paginas_normalizadas.append(normalizada)
        tamanho = caminho.stat().st_size
        fonte_url = FONTES.get(caminho.name)
        catalogo.append({
            "id_documento": document_id,
            "nome_arquivo": caminho.name,
            "caminho_relativo": f"2_corpus/{caminho.name}",
            "tamanho_bytes": tamanho,
            "hash_sha256": sha256(caminho),
            "quantidade_paginas": len(extraido["paginas"]),
            "fonte_url": fonte_url,
            "status_processamento": "processado",
        })
        extraidos.append({"id_documento": document_id, "nome_arquivo": caminho.name, "paginas": extraido["paginas"]})
        normalizados.append({"id_documento": document_id, "nome_arquivo": caminho.name, "paginas": paginas_normalizadas})
        total_paginas += len(extraido["paginas"])
        if vazias:
            avisos.append({"id_documento": document_id, "nome_arquivo": caminho.name, "paginas_vazias": vazias})
    return catalogo, extraidos, normalizados, total_paginas, avisos


def salvar(caminho, dados):
    """Grava um artefato estruturado em JSON UTF-8."""
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    """Executa a etapa Documentos → Extração → Normalização."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("2_corpus"))
    parser.add_argument("--saida", type=Path, default=Path("3_dados"))
    args = parser.parse_args()
    arquivos = sorted(args.corpus.glob("*.pdf"))
    if not arquivos:
        raise SystemExit(f"Nenhum PDF encontrado em {args.corpus}")
    args.saida.mkdir(parents=True, exist_ok=True)
    # Mede o tempo total do processamento do corpus.
    inicio = time.perf_counter()
    # Lê os PDFs e prepara os três artefatos principais.
    catalogo, extraidos, normalizados, total_paginas, avisos = construir_saida(args.corpus)
    # Persiste os resultados para as próximas etapas do pipeline.
    salvar(args.saida / "catalogo_documentos.json", {"documentos": catalogo})
    salvar(args.saida / "documentos_extraidos.json", {"documentos": extraidos})
    salvar(args.saida / "documentos_normalizados.json", {"documentos": normalizados})
    relatorio = {
        "status_pipeline": "concluido",
        "quantidade_documentos": len(catalogo),
        "quantidade_paginas": total_paginas,
        "quantidade_paginas_vazias": sum(len(item["paginas_vazias"]) for item in avisos),
        "tempo_processamento_segundos": round(time.perf_counter() - inicio, 6),
        "avisos": avisos,
        "regras_normalizacao": [
            "Unicode NFC",
            "quebras de linha padronizadas",
            "espacos repetidos reduzidos",
            "hifenizacao entre linhas recomposta",
            "texto original preservado",
        ],
    }
    salvar(args.saida / "relatorio_processamento.json", relatorio)
    assert len(catalogo) == 7, "O corpus deve conter 7 documentos"
    assert total_paginas == 83, "O corpus deve conter 83 paginas"
    print(f"Processados {len(catalogo)} documentos e {total_paginas} paginas.")
    print(f"Paginas vazias identificadas: {relatorio['quantidade_paginas_vazias']}.")


if __name__ == "__main__":
    main()
