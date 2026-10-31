"""AV2 — Etapa 5: contexto organizado para LLM e análise de tokens.

Esta etapa integra as seleções da Etapa 2 (guloso) e da Etapa 3 (PD) a um
payload de chat compatível com LLMs. Ela NÃO chama serviço externo: produz as
mensagens e mede o custo do contexto.

Pontos metodológicos:

1. `W` da AV2 é a soma dos custos individuais `w_i` dos chunks. Ele NÃO é a
   janela da LLM. Instruções, citações, separadores, pergunta e resposta são
   custos adicionais e precisam ser medidos à parte.
2. `w_i` foi calculado com `tiktoken==0.14.0`, `cl100k_base`,
   `encode_ordinary`. A etapa verifica cada `w_i` contra o texto preservado e
   recontar o prompt final com o mesmo tokenizer, pois a concatenação pode
   alterar a tokenização nas bordas.
3. Cada seletor produz um conjunto para `W ∈ {512, 1024, 2048, 4096}`. A
   etapa compara:
   - as duas seleções (guloso e PD);
   - o contexto integral (pode estourar a janela);
   - o contexto ajustado ao orçamento da LLM (descarta/trunca o que não cabe);
   - com e sem deduplicação da sobreposição de 30 palavras entre chunks.
4. As janelas analisadas são 1 024, 2 048, 4 096, 8 192 e 16 384 tokens, com
   reserva configurável para resposta e margem de segurança.

Saídas principais:
- `av2/7_contexto_llm/contextos.json` — payloads de chat dos cenários de
  exportação;
- `av2/7_contexto_llm/tabela_contexto_llm.csv` — uma linha por execução;
- `av2/7_contexto_llm/prompt_exemplo.md` — prompt legível;
- `av2/5_resultados/relatorio_contexto_llm.json` — orçamento, validação de
  `w_i`, benchmark dos seletores, comparação de métodos e resumo da matriz;
- gráficos opcionais em `av2/7_contexto_llm/`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import re
import statistics
import sys
import time
import tracemalloc
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import tiktoken


RAIZ = Path(__file__).resolve().parents[2]
DIRETORIO_AV2 = RAIZ / "av2"

CAMINHO_CHUNKS = DIRETORIO_AV2 / "2_dados_tokenizados" / "chunks_tokenizados.json"
CAMINHO_INSTANCIAS = DIRETORIO_AV2 / "3_instancias" / "instancias.json"
CAMINHOS_SELECAO = {
    "guloso": DIRETORIO_AV2 / "4_selecao_contexto" / "selecao_gulosa.json",
    "pd": DIRETORIO_AV2 / "4_selecao_contexto" / "selecao_pd.json",
}
CAMINHOS_RELATORIO_SELECAO = {
    "guloso": DIRETORIO_AV2 / "5_resultados" / "relatorio_guloso.json",
    "pd": DIRETORIO_AV2 / "5_resultados" / "relatorio_pd.json",
}
CAMINHO_CANDIDATOS_AV1 = RAIZ / "av1" / "6_busca_lexical" / "candidatos_busca.json"
DIRETORIO_SAIDA = DIRETORIO_AV2 / "7_contexto_llm"
CAMINHO_RELATORIO = DIRETORIO_AV2 / "5_resultados" / "relatorio_contexto_llm.json"

JANELAS_PADRAO = (1024, 2048, 4096, 8192, 16384)
ESTRATEGIAS = ("integral", "ajustado")
MIN_PALAVRAS_TRUNCADAS = 20

PADRAO_PALAVRA = re.compile(r"\S+", re.UNICODE)
PADRAO_TERMO = re.compile(r"[^\W_]+", re.UNICODE)

INSTRUCOES_SISTEMA = (
    "Você é um assistente de pesquisa que responde em português do Brasil.\n"
    "Use exclusivamente as evidências do CONTEXTO fornecido.\n"
    "Regras:\n"
    "1. Cite cada afirmação com o rótulo da fonte entre colchetes, por exemplo [F1].\n"
    "2. Se o contexto não contiver a resposta, escreva exatamente "
    "\"Não há evidência suficiente no contexto recuperado.\" e não complete "
    "com conhecimento externo.\n"
    "3. Preserve números, prazos e nomes exatamente como aparecem nas fontes.\n"
    "4. Não invente referências, páginas ou trechos."
)

PREFIXO_USUARIO = "CONTEXTO RECUPERADO:\n\n"
SUFIXO_USUARIO = (
    "\n\nPERGUNTA: {consulta}\n\n"
    "Responda apenas com base nas fontes acima e cite os rótulos [F1], [F2], ..."
)


# ==============================================================================
# 1. TOKENIZAÇÃO E PROVENIÊNCIA
# ==============================================================================

def contar_tokens(texto: str, encoding) -> int:
    """Conta tokens com `encode_ordinary`, o mesmo método da preparação da AV2.

    `encode_ordinary` trata marcadores como `<|endoftext|>` como texto comum,
    preservando o contrato de que o corpus não é reinterpretado como comando.
    """
    return len(encoding.encode_ordinary(texto))


def carregar_json(caminho: Path) -> dict:
    """Lê um JSON UTF-8 e devolve o objeto."""
    if not caminho.exists():
        raise FileNotFoundError(f"Artefato não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def sha256_arquivo(caminho: Path) -> str:
    """Calcula o SHA-256 de um arquivo de entrada."""
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def verificar_w_i(chunks: list[dict], encoding) -> dict:
    """Verifica `w_i` de todos os chunks contra o tokenizer fixado.

    A AV2 garante que `w_i` é a contagem exata de `encode_ordinary` do texto
    original. Se essa igualdade quebrar, o orçamento e todos os resultados da
    mochila deixam de ser comparáveis; por isso o erro é fatal.
    """
    total = 0
    zeros = 0
    for chunk in chunks:
        cid = chunk.get("id_chunk")
        w_i = chunk.get("w_i")
        if not isinstance(cid, str) or not cid:
            raise ValueError("Chunk sem id_chunk válido.")
        if type(w_i) is not int or w_i < 0:
            raise ValueError(f"w_i inválido em {cid}: {w_i!r}")
        calculado = contar_tokens(chunk.get("texto", ""), encoding)
        if calculado != w_i:
            raise ValueError(
                f"w_i divergente em {cid}: metadado={w_i}, "
                f"encode_ordinary={calculado}."
            )
        total += w_i
        zeros += int(w_i == 0)
    return {
        "total_chunks": len(chunks),
        "tokens_individuais_total": total,
        "chunks_com_w_i_zero": zeros,
    }


def carregar_termos_consulta(consulta: str) -> list[str]:
    """Obtém os termos distintos da consulta registrados pela busca da AV1.

    Usa o artefato da AV1 quando disponível e, como fallback, tokeniza a própria
    consulta removendo um pequeno conjunto de palavras funcionais.
    """
    if CAMINHO_CANDIDATOS_AV1.exists():
        metadados = carregar_json(CAMINHO_CANDIDATOS_AV1).get("metadados", {})
        termos = metadados.get("termos_distintos_consulta")
        if isinstance(termos, list) and termos and metadados.get("consulta") == consulta:
            return [str(t) for t in termos]

    stopwords = {
        "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em",
        "para", "por", "com", "sem", "que", "um", "uma", "ao", "à", "às",
    }
    return [
        termo
        for termo in PADRAO_TERMO.findall(unicodedata.normalize("NFC", consulta).casefold())
        if termo not in stopwords
    ]


# ==============================================================================
# 2. TEXTO, OFFSETS E DEDUPLICAÇÃO
# ==============================================================================

def intervalos_mesclados(intervalos: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Une intervalos [início, fim) possivelmente sobrepostos."""
    if not intervalos:
        return []
    ordenados = sorted(intervalos)
    resultado = [list(ordenados[0])]
    for inicio, fim in ordenados[1:]:
        if inicio <= resultado[-1][1]:
            resultado[-1][1] = max(resultado[-1][1], fim)
        else:
            resultado.append([inicio, fim])
    return [(inicio, fim) for inicio, fim in resultado]


def subtrair_intervalo(
    inicio: int,
    fim: int,
    cobertos: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Devolve as partes de [início, fim) ainda não cobertas."""
    livres: list[tuple[int, int]] = []
    cursor = inicio
    for coberto_inicio, coberto_fim in intervalos_mesclados(cobertos):
        if coberto_fim <= cursor:
            continue
        if coberto_inicio >= fim:
            break
        if coberto_inicio > cursor:
            livres.append((cursor, min(coberto_inicio, fim)))
        cursor = max(cursor, coberto_fim)
        if cursor >= fim:
            break
    if cursor < fim:
        livres.append((cursor, fim))
    return livres


def recortar_sobreposicao(
    texto: str,
    inicio_global: int,
    fim_global: int,
    cobertos: list[tuple[int, int]],
) -> tuple[str, list[tuple[str, tuple[int, int], int]], int]:
    """Remove de um chunk as palavras já incluídas por chunks anteriores.

    Retorna `(texto_recortado, segmentos, palavras_removidas)`. Cada segmento é
    `(texto, intervalo_global, quantidade_de_palavras)`. Os intervalos reais são
    preservados para que a cobertura dos próximos chunks não seja deslocada.
    """
    posicoes = [(m.start(), m.end()) for m in PADRAO_PALAVRA.finditer(texto)]
    if not posicoes:
        return "", [], 0

    total_palavras = len(posicoes)
    segmentos: list[tuple[str, tuple[int, int], int]] = []

    for livre_inicio, livre_fim in subtrair_intervalo(inicio_global, fim_global, cobertos):
        primeiro = max(0, livre_inicio - inicio_global)
        ultimo = min(total_palavras, livre_fim - inicio_global)
        if ultimo <= primeiro:
            continue
        segmentos.append(
            (
                texto[posicoes[primeiro][0] : posicoes[ultimo - 1][1]],
                (inicio_global + primeiro, inicio_global + ultimo),
                ultimo - primeiro,
            )
        )

    mantidas = sum(segmento[2] for segmento in segmentos)
    return "\n".join(segmento[0] for segmento in segmentos), segmentos, total_palavras - mantidas


def limitar_segmentos(
    segmentos: list[tuple[str, tuple[int, int], int]],
    limite_palavras: int,
) -> tuple[str, list[tuple[int, int]]]:
    """Mantém apenas as primeiras `limite_palavras` palavras dos segmentos."""
    partes: list[str] = []
    intervalos: list[tuple[int, int]] = []
    restante = limite_palavras

    for texto_segmento, (inicio_global, _), quantidade in segmentos:
        if restante <= 0:
            break
        usar = min(quantidade, restante)
        posicoes = [(m.start(), m.end()) for m in PADRAO_PALAVRA.finditer(texto_segmento)]
        partes.append(texto_segmento[: posicoes[usar - 1][1]])
        intervalos.append((inicio_global, inicio_global + usar))
        restante -= usar

    texto = "\n".join(partes)
    if restante == 0:
        texto += " […]"
    return texto, intervalos


def truncar_texto_para_orcamento(
    cabecalho: str,
    texto: str,
    orcamento: int,
    encoding,
) -> tuple[str, int] | None:
    """Maior número de palavras que cabe no orçamento, com busca binária."""
    posicoes = [(m.start(), m.end()) for m in PADRAO_PALAVRA.finditer(texto)]
    if not posicoes:
        return None

    melhor = 0
    esquerda, direita = 1, len(posicoes)
    while esquerda <= direita:
        meio = (esquerda + direita) // 2
        recorte = texto[: posicoes[meio - 1][1]] + " […]"
        if contar_tokens(f"{cabecalho}\n{recorte}", encoding) <= orcamento:
            melhor = meio
            esquerda = meio + 1
        else:
            direita = meio - 1

    if melhor < MIN_PALAVRAS_TRUNCADAS:
        return None
    return texto[: posicoes[melhor - 1][1]] + " […]", melhor


# ==============================================================================
# 3. ORÇAMENTO E BLOCOS
# ==============================================================================

@dataclass(frozen=True)
class OrcamentoLLM:
    """Orçamento de uma chamada de chat."""

    janela: int
    tokens_fixos: int
    reserva_resposta: int
    reserva_seguranca: int
    orcamento_contexto: int

    def como_dicionario(self) -> dict:
        return {
            "janela_llm": self.janela,
            "tokens_fixos_prompt": self.tokens_fixos,
            "reserva_resposta": self.reserva_resposta,
            "reserva_seguranca": self.reserva_seguranca,
            "orcamento_contexto": self.orcamento_contexto,
        }


def calcular_orcamento_llm(
    janela: int,
    tokens_fixos: int,
    reserva_resposta: int,
    reserva_seguranca: int,
) -> OrcamentoLLM:
    """Calcula o espaço disponível para chunks dentro da janela da LLM.

    O orçamento pode ser negativo: nesse caso o próprio prompt fixo mais a
    resposta não cabe na janela. O cenário é registrado como inviável, pois isso
    é um resultado experimental relevante, não um erro de entrada.
    """
    if janela <= 0:
        raise ValueError("A janela da LLM deve ser positiva.")
    if min(tokens_fixos, reserva_resposta, reserva_seguranca) < 0:
        raise ValueError("Tokens fixos e reservas não podem ser negativos.")
    return OrcamentoLLM(
        janela=janela,
        tokens_fixos=tokens_fixos,
        reserva_resposta=reserva_resposta,
        reserva_seguranca=reserva_seguranca,
        orcamento_contexto=janela - tokens_fixos - reserva_resposta - reserva_seguranca,
    )


@dataclass
class BlocoFonte:
    """Chunk efetivamente representado no prompt."""

    rotulo: str
    id_chunk: str
    id_documento: str
    nome_arquivo: str
    paginas: list[int]
    v_i: float
    w_i: int
    texto: str
    cabecalho: str
    tokens_texto_original: int
    tokens_texto: int
    tokens_bloco: int
    palavras_incluidas: int
    palavras_removidas_sobreposicao: int
    truncado: bool = False

    def renderizar(self) -> str:
        return f"{self.cabecalho}\n{self.texto}"

    def como_dicionario(self) -> dict:
        return {
            "rotulo": self.rotulo,
            "id_chunk": self.id_chunk,
            "id_documento": self.id_documento,
            "nome_arquivo": self.nome_arquivo,
            "paginas": self.paginas,
            "v_i": self.v_i,
            "w_i": self.w_i,
            "tokens_texto_original": self.tokens_texto_original,
            "tokens_texto": self.tokens_texto,
            "tokens_bloco": self.tokens_bloco,
            "palavras_incluidas": self.palavras_incluidas,
            "palavras_removidas_sobreposicao": self.palavras_removidas_sobreposicao,
            "truncado": self.truncado,
            "texto": self.texto,
        }


def montar_cabecalho(rotulo: str, chunk: dict) -> str:
    """Cabeçalho de citação com documento, páginas, chunk e relevância."""
    paginas = ", ".join(str(p) for p in chunk.get("paginas", [])) or "?"
    return (
        f"[{rotulo}] {chunk.get('nome_arquivo', 'documento desconhecido')} "
        f"| páginas {paginas} "
        f"| {chunk.get('id_chunk', '?')} "
        f"| BM25 {float(chunk.get('v_i', 0.0)):.4f}"
    )


def criar_bloco(
    chunk: dict,
    rotulo: str,
    cobertos: list[tuple[int, int]],
    deduplicar: bool,
    orcamento_restante: int | None,
    truncar: bool,
    encoding,
) -> tuple[BlocoFonte | None, list[tuple[int, int]], str]:
    """Cria um bloco, aplicando deduplicação e, se necessário, truncamento.

    Retorna `(bloco, intervalos_reais_incluidos, motivo_descarte)`.
    """
    inicio = int(chunk.get("inicio_palavra", 0))
    fim = int(chunk.get("fim_palavra", inicio + int(chunk.get("quantidade_palavras", 0))))
    texto_original = str(chunk.get("texto", ""))
    tokens_texto_original = contar_tokens(texto_original, encoding)

    if deduplicar:
        texto, segmentos, removidas = recortar_sobreposicao(
            texto_original, inicio, fim, cobertos
        )
        if not texto:
            return None, [], "sobreposicao_total"
    else:
        palavras = sum(1 for _ in PADRAO_PALAVRA.finditer(texto_original))
        segmentos = [(texto_original, (inicio, fim), palavras)]
        texto = texto_original
        removidas = 0

    palavras_incluidas = sum(segmento[2] for segmento in segmentos)
    cabecalho = montar_cabecalho(rotulo, chunk)
    tokens_texto = contar_tokens(texto, encoding)
    tokens_bloco = contar_tokens(f"{cabecalho}\n{texto}", encoding)
    truncado = False

    if orcamento_restante is not None and tokens_bloco > orcamento_restante:
        if not truncar:
            return None, [], "orcamento"
        recorte = truncar_texto_para_orcamento(
            cabecalho, texto, orcamento_restante, encoding
        )
        if recorte is None:
            return None, [], "orcamento"
        _, palavras_incluidas = recorte
        texto, intervalos = limitar_segmentos(segmentos, palavras_incluidas)
        tokens_texto = contar_tokens(texto, encoding)
        tokens_bloco = contar_tokens(f"{cabecalho}\n{texto}", encoding)
        while (
            tokens_bloco > orcamento_restante
            and palavras_incluidas > MIN_PALAVRAS_TRUNCADAS
        ):
            palavras_incluidas -= 1
            texto, intervalos = limitar_segmentos(segmentos, palavras_incluidas)
            tokens_texto = contar_tokens(texto, encoding)
            tokens_bloco = contar_tokens(f"{cabecalho}\n{texto}", encoding)
        if tokens_bloco > orcamento_restante:
            return None, [], "orcamento"
        truncado = True
    else:
        intervalos = [segmento[1] for segmento in segmentos]

    bloco = BlocoFonte(
        rotulo=rotulo,
        id_chunk=str(chunk.get("id_chunk", "")),
        id_documento=str(chunk.get("id_documento", "")),
        nome_arquivo=str(chunk.get("nome_arquivo", "")),
        paginas=list(chunk.get("paginas", [])),
        v_i=float(chunk.get("v_i", 0.0)),
        w_i=int(chunk.get("w_i", 0)),
        texto=texto,
        cabecalho=cabecalho,
        tokens_texto_original=tokens_texto_original,
        tokens_texto=tokens_texto,
        tokens_bloco=tokens_bloco,
        palavras_incluidas=palavras_incluidas,
        palavras_removidas_sobreposicao=removidas,
        truncado=truncado,
    )
    return bloco, intervalos, ""


# ==============================================================================
# 4. MONTAGEM DO PROMPT E MÉTRICAS
# ==============================================================================

def medir_tokens_fixos(consulta: str, encoding) -> int:
    """Custo do prompt do sistema e da moldura da pergunta, sem contexto."""
    return contar_tokens(INSTRUCOES_SISTEMA, encoding) + contar_tokens(
        PREFIXO_USUARIO + SUFIXO_USUARIO.format(consulta=consulta), encoding
    )


def montar_mensagens(consulta: str, blocos: list[BlocoFonte]) -> tuple[list[dict], str, str]:
    """Monta as mensagens de chat e devolve também o texto do usuário e o prompt."""
    contexto = "\n\n".join(bloco.renderizar() for bloco in blocos)
    mensagem_usuario = f"{PREFIXO_USUARIO}{contexto}{SUFIXO_USUARIO.format(consulta=consulta)}"
    mensagens = [
        {"role": "system", "content": INSTRUCOES_SISTEMA},
        {"role": "user", "content": mensagem_usuario},
    ]
    prompt_texto = f"# system\n{INSTRUCOES_SISTEMA}\n\n# user\n{mensagem_usuario}"
    return mensagens, mensagem_usuario, prompt_texto


def taxa_redundancia_ngramas(texto: str, n: int = 5) -> float:
    """Fração de n-gramas repetidos no texto (0 = sem repetição)."""
    palavras = [
        p.casefold()
        for p in PADRAO_TERMO.findall(unicodedata.normalize("NFC", texto))
    ]
    if len(palavras) < n:
        return 0.0
    ngramas = [tuple(palavras[i : i + n]) for i in range(len(palavras) - n + 1)]
    return 1.0 - (len(set(ngramas)) / len(ngramas))


def calcular_metricas_qualidade(
    blocos: list[BlocoFonte],
    termos_consulta: list[str],
    tokens_prompt: int,
    relevancia_incluida: float,
) -> dict:
    """Proxies offline de cobertura e redundância; não avaliam a resposta."""
    texto = "\n".join(bloco.texto for bloco in blocos)
    tokens_texto = PADRAO_TERMO.findall(
        unicodedata.normalize("NFC", texto).casefold()
    )
    conjunto = set(tokens_texto)
    termos = [t.casefold() for t in termos_consulta]
    cobertos = [t for t in termos if t in conjunto]
    frequencia = sum(tokens_texto.count(t) for t in termos)
    documentos = {bloco.id_documento for bloco in blocos}

    return {
        "chunks_incluidos": len(blocos),
        "chunks_truncados": sum(1 for bloco in blocos if bloco.truncado),
        "palavras_contexto": sum(bloco.palavras_incluidas for bloco in blocos),
        "palavras_removidas_sobreposicao": sum(
            bloco.palavras_removidas_sobreposicao for bloco in blocos
        ),
        "cobertura_termos": round(len(cobertos) / len(termos), 4) if termos else 0.0,
        "termos_cobertos": cobertos,
        "termos_ausentes": [t for t in termos if t not in conjunto],
        "frequencia_termos": frequencia,
        "densidade_termos_por_1000_tokens": (
            round(frequencia / tokens_prompt * 1000, 4) if tokens_prompt else 0.0
        ),
        "documentos_distintos": len(documentos),
        "diversidade_documentos": (
            round(len(documentos) / len(blocos), 4) if blocos else 0.0
        ),
        "redundancia_ngramas_5": round(taxa_redundancia_ngramas(texto, 5), 4),
        "relevancia_incluida": round(relevancia_incluida, 4),
        "relevancia_por_1000_tokens_prompt": (
            round(relevancia_incluida / tokens_prompt * 1000, 4) if tokens_prompt else 0.0
        ),
    }


def estimar_latencia(
    tokens_entrada: int,
    tokens_saida: int,
    taxa_prefill: float,
    taxa_decode: float,
) -> dict:
    """Latência linear por token; a atenção quadrática é discutida no documento."""
    if taxa_prefill <= 0 or taxa_decode <= 0:
        raise ValueError("As taxas de prefill e decode devem ser positivas.")
    prefill = tokens_entrada / taxa_prefill
    decode = tokens_saida / taxa_decode
    return {
        "tokens_entrada": tokens_entrada,
        "tokens_saida_reservados": tokens_saida,
        "taxa_prefill_tokens_por_segundo": taxa_prefill,
        "taxa_decode_tokens_por_segundo": taxa_decode,
        "latencia_prefill_s": round(prefill, 4),
        "latencia_decode_s": round(decode, 4),
        "latencia_total_s": round(prefill + decode, 4),
    }


def ordenar_selecionados(
    selecionados: list[dict],
    chunks_map: dict[str, dict],
    ordem: str,
) -> list[dict]:
    """Ordena os chunks para o prompt, sem alterar o conjunto selecionado."""
    if ordem == "relevancia":
        return sorted(selecionados, key=lambda c: (-float(c.get("v_i", 0.0)), c["id_chunk"]))
    if ordem == "selecao":
        return sorted(selecionados, key=lambda c: int(c.get("ordem_selecao", 0)))
    if ordem == "corpus":
        return sorted(
            selecionados,
            key=lambda c: int(chunks_map[c["id_chunk"]].get("ordem_global", 0)),
        )
    raise ValueError(f"Ordem desconhecida: {ordem}")


def textos_deduplicados_selecionados(
    selecionados: list[dict],
    chunks_map: dict[str, dict],
    encoding,
) -> tuple[int, int]:
    """Conta tokens dos textos deduplicados de toda a seleção.

    É uma medida do potencial de economia da deduplicação, independente do
    orçamento da LLM. Retorna `(tokens, palavras_removidas)`.
    """
    cobertos_por_documento: dict[str, list[tuple[int, int]]] = {}
    textos: list[str] = []
    removidas = 0
    for selecionado in selecionados:
        chunk = chunks_map[selecionado["id_chunk"]]
        documento = str(chunk.get("id_documento", ""))
        cobertos = cobertos_por_documento.setdefault(documento, [])
        inicio = int(chunk.get("inicio_palavra", 0))
        fim = int(chunk.get("fim_palavra", inicio + int(chunk.get("quantidade_palavras", 0))))
        texto, segmentos, removidas_chunk = recortar_sobreposicao(
            str(chunk.get("texto", "")), inicio, fim, cobertos
        )
        textos.append(texto)
        removidas += removidas_chunk
        cobertos.extend(segmento[1] for segmento in segmentos)
    return contar_tokens("\n\n".join(textos), encoding), removidas


@dataclass
class ResultadoCenario:
    """Resultado completo de um cenário seletor × W × janela × estratégia."""

    seletor: str
    W: int
    janela: int
    estrategia: str
    deduplicar: bool
    ordem: str
    consulta: str
    orcamento: OrcamentoLLM
    blocos: list[BlocoFonte]
    mensagens: list[dict]
    prompt_texto: str
    tokens_textos_selecionados: int
    tokens_w_i_selecionados: int
    tokens_textos_deduplicados: int
    palavras_removidas_sobreposicao: int
    tokens_w_i_incluidos: int
    tokens_textos_incluidos: int
    tokens_contexto: int
    tokens_prompt: int
    chunks_selecionados: int
    chunks_descartados: int
    relevancia_selecionada: float
    relevancia_incluida: float
    metricas: dict = field(default_factory=dict)

    @property
    def folga_llm(self) -> int:
        return (
            self.janela
            - self.tokens_prompt
            - self.orcamento.reserva_resposta
            - self.orcamento.reserva_seguranca
        )

    @property
    def estourou_janela(self) -> bool:
        return self.folga_llm < 0

    @property
    def overhead_prompt(self) -> int:
        return self.tokens_prompt - self.tokens_textos_incluidos

    @property
    def overhead_vs_w_i(self) -> int:
        return self.tokens_prompt - self.tokens_w_i_incluidos

    @property
    def delta_borda(self) -> int:
        return self.tokens_textos_incluidos - self.tokens_w_i_incluidos

    @property
    def economia_dedupe(self) -> int:
        """Economia potencial da seleção, independente de a dedupe ser aplicada."""
        return self.tokens_textos_selecionados - self.tokens_textos_deduplicados

    @property
    def economia_dedupe_aplicada(self) -> int:
        """Economia efetivamente aplicada aos blocos incluídos no prompt."""
        if not self.deduplicar:
            return 0
        return sum(
            bloco.tokens_texto_original - bloco.tokens_texto
            for bloco in self.blocos
            if not bloco.truncado
        )

    @property
    def perda_relevancia_janela(self) -> float:
        return round(self.relevancia_selecionada - self.relevancia_incluida, 4)

    def como_dicionario(self) -> dict:
        return {
            "seletor": self.seletor,
            "W": self.W,
            "janela_llm": self.janela,
            "estrategia": self.estrategia,
            "deduplicar": self.deduplicar,
            "ordem": self.ordem,
            "chunks_selecionados": self.chunks_selecionados,
            "chunks_incluidos": len(self.blocos),
            "chunks_descartados_janela": self.chunks_descartados,
            "chunks_truncados": self.metricas.get("chunks_truncados", 0),
            "tokens_w_i_selecionados": self.tokens_w_i_selecionados,
            "tokens_textos_selecionados": self.tokens_textos_selecionados,
            "tokens_textos_deduplicados": self.tokens_textos_deduplicados,
            "economia_dedupe_potencial": self.economia_dedupe,
            "economia_dedupe_aplicada": self.economia_dedupe_aplicada,
            "palavras_removidas_sobreposicao": self.palavras_removidas_sobreposicao,
            "tokens_w_i_incluidos": self.tokens_w_i_incluidos,
            "tokens_textos_incluidos": self.tokens_textos_incluidos,
            "tokens_contexto": self.tokens_contexto,
            "tokens_prompt": self.tokens_prompt,
            "tokens_fixos": self.orcamento.tokens_fixos,
            "overhead_prompt": self.overhead_prompt,
            "overhead_vs_w_i": self.overhead_vs_w_i,
            "delta_borda": self.delta_borda,
            "orcamento_contexto": self.orcamento.orcamento_contexto,
            "folga_llm": self.folga_llm,
            "estourou_janela": self.estourou_janela,
            "relevancia_selecionada": round(self.relevancia_selecionada, 4),
            "relevancia_incluida": round(self.relevancia_incluida, 4),
            "perda_relevancia_janela": self.perda_relevancia_janela,
            **self.metricas,
        }


def montar_cenario(
    seletor: str,
    cenario_selecao: dict,
    chunks_map: dict[str, dict],
    consulta: str,
    janela: int,
    estrategia: str,
    deduplicar: bool,
    ordem: str,
    encoding,
    tokens_fixos: int,
    reserva_resposta: int,
    reserva_seguranca: int,
    truncar_ultimo: bool,
    termos_consulta: list[str],
) -> ResultadoCenario:
    """Monta um cenário completo e verifica as invariantes de orçamento.

    Complexidade: O(k·m) para tokenizar/recortar k chunks de m palavras, mais
    O(C) da tokenização BPE do prompt final. Memória O(prompt).
    """
    if estrategia not in ESTRATEGIAS:
        raise ValueError(f"Estratégia desconhecida: {estrategia}")
    if seletor not in CAMINHOS_SELECAO:
        raise ValueError(f"Seletor desconhecido: {seletor}")

    selecionados = cenario_selecao.get("chunks", [])
    if not isinstance(selecionados, list):
        raise ValueError(f"Cenário de {seletor} sem lista de chunks.")
    W = cenario_selecao.get("W")
    if type(W) is not int or W < 0:
        raise ValueError(f"W inválido no cenário de {seletor}: {W!r}")

    soma_w_i = sum(int(c.get("w_i", 0)) for c in selecionados)
    if soma_w_i != cenario_selecao.get("tokens_usados"):
        raise ValueError(
            f"Soma de w_i ({soma_w_i}) difere de tokens_usados "
            f"({cenario_selecao.get('tokens_usados')}) em {seletor} W={W}."
        )

    ordenados = ordenar_selecionados(selecionados, chunks_map, ordem)
    tokens_textos_selecionados = contar_tokens(
        "\n\n".join(str(chunks_map[c["id_chunk"]]["texto"]) for c in ordenados),
        encoding,
    )
    tokens_deduplicados, palavras_removidas = textos_deduplicados_selecionados(
        ordenados, chunks_map, encoding
    )

    orcamento = calcular_orcamento_llm(
        janela, tokens_fixos, reserva_resposta, reserva_seguranca
    )
    cobertos_por_documento: dict[str, list[tuple[int, int]]] = {}
    blocos: list[BlocoFonte] = []
    descartados = 0
    descartados_sobreposicao = 0
    tokens_acumulados = 0

    for selecionado in ordenados:
        chunk = chunks_map.get(selecionado["id_chunk"])
        if chunk is None:
            raise ValueError(f"Chunk selecionado inexistente: {selecionado['id_chunk']}")
        documento = str(chunk.get("id_documento", ""))
        cobertos = cobertos_por_documento.setdefault(documento, [])
        rotulo = f"F{len(blocos) + 1}"

        if estrategia == "integral":
            restante = None
            truncar = False
        else:
            restante = orcamento.orcamento_contexto - tokens_acumulados
            if blocos:
                restante -= contar_tokens("\n\n", encoding)
            truncar = truncar_ultimo

        bloco, intervalos, motivo = criar_bloco(
            chunk=chunk,
            rotulo=rotulo,
            cobertos=cobertos,
            deduplicar=deduplicar,
            orcamento_restante=restante,
            truncar=truncar,
            encoding=encoding,
        )
        if bloco is None:
            if motivo == "orcamento":
                descartados += 1
            elif motivo == "sobreposicao_total":
                descartados_sobreposicao += 1
            continue

        if blocos:
            tokens_acumulados += contar_tokens("\n\n", encoding)
        blocos.append(bloco)
        tokens_acumulados += bloco.tokens_bloco
        cobertos.extend(intervalos)
        if bloco.truncado:
            break

    # O recorte por blocos pode deixar o prompt alguns tokens acima do orçamento
    # por causa das bordas da concatenação. Remove o último bloco até caber.
    mensagens, _, prompt_texto = montar_mensagens(consulta, blocos)
    tokens_prompt = contar_tokens(mensagens[0]["content"], encoding) + contar_tokens(
        mensagens[1]["content"], encoding
    )
    if estrategia == "ajustado":
        while (
            tokens_prompt + reserva_resposta + reserva_seguranca > janela
            and blocos
        ):
            blocos.pop()
            descartados += 1
            mensagens, _, prompt_texto = montar_mensagens(consulta, blocos)
            tokens_prompt = contar_tokens(mensagens[0]["content"], encoding) + contar_tokens(
                mensagens[1]["content"], encoding
            )

    contexto_texto = "\n\n".join(bloco.renderizar() for bloco in blocos)
    tokens_textos_incluidos = contar_tokens(
        "\n\n".join(bloco.texto for bloco in blocos), encoding
    )
    tokens_contexto = contar_tokens(contexto_texto, encoding)
    relevancia_selecionada = sum(float(c.get("v_i", 0.0)) for c in selecionados)
    relevancia_incluida = sum(bloco.v_i for bloco in blocos)

    metricas = calcular_metricas_qualidade(
        blocos=blocos,
        termos_consulta=termos_consulta,
        tokens_prompt=tokens_prompt,
        relevancia_incluida=relevancia_incluida,
    )
    metricas["chunks_selecionados"] = len(selecionados)
    metricas["chunks_descartados_janela"] = descartados
    metricas["chunks_descartados_sobreposicao"] = descartados_sobreposicao
    metricas["chunks_nao_avaliados"] = max(
        0,
        len(selecionados) - len(blocos) - descartados - descartados_sobreposicao,
    )

    return ResultadoCenario(
        seletor=seletor,
        W=W,
        janela=janela,
        estrategia=estrategia,
        deduplicar=deduplicar,
        ordem=ordem,
        consulta=consulta,
        orcamento=orcamento,
        blocos=blocos,
        mensagens=mensagens,
        prompt_texto=prompt_texto,
        tokens_textos_selecionados=tokens_textos_selecionados,
        tokens_w_i_selecionados=soma_w_i,
        tokens_textos_deduplicados=tokens_deduplicados,
        palavras_removidas_sobreposicao=palavras_removidas,
        tokens_w_i_incluidos=sum(bloco.w_i for bloco in blocos),
        tokens_textos_incluidos=tokens_textos_incluidos,
        tokens_contexto=tokens_contexto,
        tokens_prompt=tokens_prompt,
        chunks_selecionados=len(selecionados),
        chunks_descartados=descartados,
        relevancia_selecionada=relevancia_selecionada,
        relevancia_incluida=relevancia_incluida,
        metricas=metricas,
    )


# ==============================================================================
# 5. BENCHMARK DOS SELETORES E MATRIZ DE CONTEXTO
# ==============================================================================

def carregar_modulo(nome: str, caminho: Path):
    """Importa um script da AV2 sem executar seu `main`."""
    especificacao = importlib.util.spec_from_file_location(nome, caminho)
    if especificacao is None or especificacao.loader is None:
        raise ImportError(f"Não foi possível carregar {caminho}")
    modulo = importlib.util.module_from_spec(especificacao)
    sys.modules[nome] = modulo
    especificacao.loader.exec_module(modulo)
    return modulo


def medir_operacao(operacao, repeticoes: int) -> tuple[object, float, int]:
    """Executa `operacao` e devolve `(resultado, mediana_ms, pico_bytes)`."""
    tempos: list[float] = []
    resultado = None
    for _ in range(max(1, repeticoes)):
        inicio = time.perf_counter()
        resultado = operacao()
        tempos.append((time.perf_counter() - inicio) * 1000)

    tracemalloc.start()
    operacao()
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, statistics.median(tempos), pico


def benchmark_selecao(
    instancias: dict,
    selecoes: dict[str, dict],
    repeticoes: int,
) -> dict:
    """Mede tempo e memória dos dois seletores sob o mesmo harness.

    O tempo reportado pela Etapa 4 é reaproveitado no relatório; esta medição
    existe para colocar guloso e PD na mesma unidade e registrar a memória
    observada da PD (matrizes `n × W`) contra a do guloso (lista ordenada).
    """
    modulo_guloso = carregar_modulo(
        "selecionar_guloso_av2", DIRETORIO_AV2 / "1_scripts" / "selecionar_guloso.py"
    )
    modulo_pd = carregar_modulo(
        "selecionar_pd_av2", DIRETORIO_AV2 / "1_scripts" / "selecionar_pd.py"
    )
    itens = instancias["itens"]
    resultado: dict[str, list[dict]] = {"guloso": [], "pd": []}

    for instancia in instancias["instancias"]:
        W = int(instancia["W"])
        id_instancia = str(instancia["id_instancia"])

        def operacao_gulosa() -> tuple:
            return modulo_guloso.selecionar_guloso_instancia(itens, W)

        def operacao_pd() -> tuple:
            return modulo_pd.resolver_mochila_pd(itens, W)

        for seletor, operacao in (("guloso", operacao_gulosa), ("pd", operacao_pd)):
            (selecionados, tokens, relevancia, avaliados), tempo_ms, pico = medir_operacao(
                operacao, repeticoes
            )
            ids_calculados = sorted(item["id_chunk"] for item in selecionados)
            ids_artefato = sorted(
                selecoes[seletor]["cenarios"][id_instancia]["ids_selecionados"]
            )
            if ids_calculados != ids_artefato:
                raise ValueError(
                    f"Seleção recalculada difere do artefato em {seletor} {id_instancia}."
                )
            resultado[seletor].append(
                {
                    "id_instancia": id_instancia,
                    "W": W,
                    "tempo_medio_ms": round(tempo_ms, 4),
                    "memoria_pico_bytes": pico,
                    "total_chunks": len(selecionados),
                    "tokens_usados": tokens,
                    "relevancia_total": relevancia,
                    "total_avaliados": avaliados,
                }
            )
    return resultado


def executar_matriz(
    selecoes: dict[str, dict],
    chunks_map: dict[str, dict],
    consulta: str,
    encoding,
    janelas: list[int],
    estrategias: list[str],
    opcoes_dedupe: list[bool],
    ordem: str,
    tokens_fixos: int,
    reserva_resposta: int,
    reserva_seguranca: int,
    truncar_ultimo: bool,
    termos_consulta: list[str],
    repeticoes: int,
    taxa_prefill: float,
    taxa_decode: float,
) -> list[dict]:
    """Executa seletor × W × janela × estratégia × deduplicação."""
    linhas: list[dict] = []
    for seletor in ("guloso", "pd"):
        for cenario in selecoes[seletor]["cenarios"].values():
            for janela in janelas:
                for estrategia in estrategias:
                    for deduplicar in opcoes_dedupe:
                        def operacao() -> ResultadoCenario:
                            return montar_cenario(
                                seletor=seletor,
                                cenario_selecao=cenario,
                                chunks_map=chunks_map,
                                consulta=consulta,
                                janela=janela,
                                estrategia=estrategia,
                                deduplicar=deduplicar,
                                ordem=ordem,
                                encoding=encoding,
                                tokens_fixos=tokens_fixos,
                                reserva_resposta=reserva_resposta,
                                reserva_seguranca=reserva_seguranca,
                                truncar_ultimo=truncar_ultimo,
                                termos_consulta=termos_consulta,
                            )

                        resultado, tempo_ms, pico = medir_operacao(operacao, repeticoes)
                        linha = resultado.como_dicionario()
                        linha["tempo_montagem_ms"] = round(tempo_ms, 4)
                        linha["memoria_pico_bytes"] = pico
                        latencia = estimar_latencia(
                            resultado.tokens_prompt,
                            reserva_resposta,
                            taxa_prefill,
                            taxa_decode,
                        )
                        linha["latencia_prefill_s"] = latencia["latencia_prefill_s"]
                        linha["latencia_decode_s"] = latencia["latencia_decode_s"]
                        linha["latencia_total_s"] = latencia["latencia_total_s"]
                        linhas.append(linha)
    return linhas


# ==============================================================================
# 6. RELATÓRIO, EXPORTAÇÃO E GRÁFICOS
# ==============================================================================

def registrar_ambiente() -> dict:
    """Registra o ambiente das medições."""
    return {
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "plataforma": platform.platform(),
        "arquitetura": platform.machine(),
        "processador": platform.processor() or "Não identificado",
        "versao_python": platform.python_version(),
        "interpretador": sys.executable,
    }


def git(*args: str) -> str | None:
    """Executa um comando git de leitura e devolve a saída, se disponível."""
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "-C", str(RAIZ), *args],
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def resumir_por_orcamento(linhas: list[dict], janela: int) -> list[dict]:
    """Resumo por seletor e W na janela de referência, com dedupe e integral."""
    resumo: list[dict] = []
    for seletor in ("guloso", "pd"):
        for W in sorted({linha["W"] for linha in linhas}):
            filtro = [
                linha
                for linha in linhas
                if linha["seletor"] == seletor
                and linha["W"] == W
                and linha["janela_llm"] == janela
                and linha["estrategia"] == "integral"
                and linha["deduplicar"] is True
            ]
            if not filtro:
                continue
            linha = filtro[0]
            resumo.append(
                {
                    "seletor": seletor,
                    "W": W,
                    "chunks_selecionados": linha["chunks_selecionados"],
                    "tokens_w_i": linha["tokens_w_i_selecionados"],
                    "tokens_textos_recontados": linha["tokens_textos_selecionados"],
                    "tokens_contexto": linha["tokens_contexto"],
                    "tokens_prompt": linha["tokens_prompt"],
                    "overhead_prompt": linha["overhead_prompt"],
                    "delta_borda": linha["delta_borda"],
                    "economia_dedupe": linha["economia_dedupe_aplicada"],
                    "relevancia_incluida": linha["relevancia_incluida"],
                    "relevancia_por_1000_tokens_prompt": linha[
                        "relevancia_por_1000_tokens_prompt"
                    ],
                    "folga_llm": linha["folga_llm"],
                    "estourou_janela": linha["estourou_janela"],
                }
            )
    return resumo


def comparar_metodos(resumo: list[dict]) -> list[dict]:
    """Compara PD e guloso por W no mesmo cenário."""
    comparacoes: list[dict] = []
    for W in sorted({item["W"] for item in resumo}):
        guloso = next(
            (item for item in resumo if item["W"] == W and item["seletor"] == "guloso"),
            None,
        )
        pd = next(
            (item for item in resumo if item["W"] == W and item["seletor"] == "pd"),
            None,
        )
        if guloso is None or pd is None:
            continue
        comparacoes.append(
            {
                "W": W,
                "ganho_relevancia_pd": round(
                    pd["relevancia_incluida"] - guloso["relevancia_incluida"], 4
                ),
                "delta_tokens_prompt_pd": pd["tokens_prompt"] - guloso["tokens_prompt"],
                "delta_relevancia_por_1000": round(
                    pd["relevancia_por_1000_tokens_prompt"]
                    - guloso["relevancia_por_1000_tokens_prompt"],
                    4,
                ),
            }
        )
    return comparacoes


def salvar_json(caminho: Path, dados: dict) -> None:
    """Grava JSON UTF-8 com listas de páginas compactas."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False)
    texto = re.sub(
        r'"paginas":\s*\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]',
        lambda m: f'"paginas": [{", ".join(re.findall(r"\d+", m.group(1)))}]',
        texto,
    )
    caminho.write_text(texto + "\n", encoding="utf-8")


def salvar_csv(caminho: Path, linhas: list[dict]) -> None:
    """Grava a matriz experimental em CSV."""
    if not linhas:
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)


def exportar_contextos(
    selecoes: dict[str, dict],
    chunks_map: dict[str, dict],
    consulta: str,
    encoding,
    tokens_fixos: int,
    janela: int,
    estrategia: str,
    deduplicar: bool,
    ordem: str,
    reserva_resposta: int,
    reserva_seguranca: int,
    truncar_ultimo: bool,
    termos_consulta: list[str],
    modelo: str,
) -> dict:
    """Exporta payloads de chat para cada seletor e W na janela escolhida."""
    cenarios: dict[str, dict] = {}
    for seletor in ("guloso", "pd"):
        for cenario in selecoes[seletor]["cenarios"].values():
            resultado = montar_cenario(
                seletor=seletor,
                cenario_selecao=cenario,
                chunks_map=chunks_map,
                consulta=consulta,
                janela=janela,
                estrategia=estrategia,
                deduplicar=deduplicar,
                ordem=ordem,
                encoding=encoding,
                tokens_fixos=tokens_fixos,
                reserva_resposta=reserva_resposta,
                reserva_seguranca=reserva_seguranca,
                truncar_ultimo=truncar_ultimo,
                termos_consulta=termos_consulta,
            )
            chave = f"{seletor}|W_{resultado.W}"
            cenarios[chave] = {
                "mensagens": resultado.mensagens,
                "uso_sugerido": {
                    "model": modelo,
                    "max_tokens": reserva_resposta,
                    "temperature": 0.0,
                },
                "fontes": [
                    {
                        campo: valor
                        for campo, valor in bloco.como_dicionario().items()
                        if campo != "texto"
                    }
                    for bloco in resultado.blocos
                ],
                "metricas": resultado.como_dicionario(),
            }
    return {"metadados": {"janela_llm": janela, "estrategia": estrategia,
                          "deduplicar": deduplicar, "ordem": ordem}, "cenarios": cenarios}


def salvar_prompt_exemplo(
    caminho: Path,
    resultado: ResultadoCenario,
) -> None:
    """Grava um prompt legível para inspeção."""
    linhas = [
        f"# Contexto para LLM — {resultado.seletor.upper()} / W={resultado.W}",
        "",
        f"- Janela: {resultado.janela}",
        f"- Estratégia: {resultado.estrategia}",
        f"- Deduplicação: {resultado.deduplicar}",
        f"- Ordem: {resultado.ordem}",
        f"- Tokens de contexto: {resultado.tokens_contexto}",
        f"- Tokens do prompt: {resultado.tokens_prompt}",
        f"- Folga da janela: {resultado.folga_llm}",
        "",
        "## Prompt do sistema",
        "",
        "```text",
        INSTRUCOES_SISTEMA,
        "```",
        "",
        "## Mensagem do usuário",
        "",
        "```text",
        resultado.mensagens[1]["content"],
        "```",
        "",
    ]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas), encoding="utf-8")


def gerar_graficos(linhas: list[dict], diretorio: Path) -> list[str]:
    """Gera gráficos de tokens, folga e latência, se matplotlib existir."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    diretorio.mkdir(parents=True, exist_ok=True)
    caminhos: list[str] = []

    # 1) Prompt por W, na janela 8192, dedupe, estratégia integral.
    serie = [
        linha
        for linha in linhas
        if linha["janela_llm"] == 8192
        and linha["estrategia"] == "integral"
        and linha["deduplicar"] is True
    ]
    if serie:
        figura, eixo = plt.subplots(figsize=(8, 4.5))
        for seletor in ("guloso", "pd"):
            pontos = sorted(
                (linha for linha in serie if linha["seletor"] == seletor),
                key=lambda item: item["W"],
            )
            eixo.plot(
                [p["W"] for p in pontos],
                [p["tokens_prompt"] for p in pontos],
                marker="o",
                label=seletor,
            )
        eixo.set_xlabel("W (orçamento de seleção, tokens w_i)")
        eixo.set_ylabel("tokens do prompt final")
        eixo.set_title("Prompt final por W e seletor (janela 8 192, dedupe)")
        eixo.grid(True, alpha=0.3)
        eixo.legend(fontsize=8)
        figura.tight_layout()
        caminho = diretorio / "grafico_prompt_por_w.png"
        figura.savefig(caminho, dpi=150)
        plt.close(figura)
        caminhos.append(str(caminho))

    # 2) Folga da janela por W e janela, PD ajustado com dedupe.
    serie = [
        linha
        for linha in linhas
        if linha["seletor"] == "pd"
        and linha["estrategia"] == "ajustado"
        and linha["deduplicar"] is True
    ]
    if serie:
        figura, eixo = plt.subplots(figsize=(8, 4.5))
        for W in sorted({linha["W"] for linha in serie}):
            pontos = sorted(
                (linha for linha in serie if linha["W"] == W),
                key=lambda item: item["janela_llm"],
            )
            eixo.plot(
                [p["janela_llm"] for p in pontos],
                [p["folga_llm"] for p in pontos],
                marker="o",
                label=f"W={W}",
            )
        eixo.axhline(0, color="black", linewidth=0.8)
        eixo.set_xscale("log", base=2)
        eixo.set_xlabel("janela da LLM (tokens)")
        eixo.set_ylabel("folga após resposta e segurança")
        eixo.set_title("Folga da janela — PD ajustado com deduplicação")
        eixo.grid(True, alpha=0.3)
        eixo.legend(fontsize=8)
        figura.tight_layout()
        caminho = diretorio / "grafico_folga_janela.png"
        figura.savefig(caminho, dpi=150)
        plt.close(figura)
        caminhos.append(str(caminho))

    # 3) Latência estimada versus tokens do prompt.
    if linhas:
        figura, eixo = plt.subplots(figsize=(8, 4.5))
        for seletor in ("guloso", "pd"):
            pontos = [linha for linha in linhas if linha["seletor"] == seletor]
            eixo.scatter(
                [p["tokens_prompt"] for p in pontos],
                [p["latencia_total_s"] for p in pontos],
                s=12,
                alpha=0.6,
                label=seletor,
            )
        eixo.set_xlabel("tokens de entrada no prompt")
        eixo.set_ylabel("latência estimada (s)")
        eixo.set_title("Latência estimada versus tamanho do prompt")
        eixo.grid(True, alpha=0.3)
        eixo.legend(fontsize=8)
        figura.tight_layout()
        caminho = diretorio / "grafico_latencia_contexto.png"
        figura.savefig(caminho, dpi=150)
        plt.close(figura)
        caminhos.append(str(caminho))

    return caminhos


# ==============================================================================
# 7. LINHA DE COMANDO
# ==============================================================================

def construir_parser() -> argparse.ArgumentParser:
    """Define a interface de linha de comando."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=CAMINHO_CHUNKS)
    parser.add_argument("--instancias", type=Path, default=CAMINHO_INSTANCIAS)
    parser.add_argument("--selecao-gulosa", type=Path, default=CAMINHOS_SELECAO["guloso"])
    parser.add_argument("--selecao-pd", type=Path, default=CAMINHOS_SELECAO["pd"])
    parser.add_argument("--saida", type=Path, default=DIRETORIO_SAIDA)
    parser.add_argument("--relatorio", type=Path, default=CAMINHO_RELATORIO)
    parser.add_argument(
        "--janelas", type=int, nargs="+", default=list(JANELAS_PADRAO),
        help="Janelas de LLM a analisar.",
    )
    parser.add_argument(
        "--estrategias", nargs="+", choices=ESTRATEGIAS, default=list(ESTRATEGIAS),
    )
    parser.add_argument(
        "--ordem", choices=("relevancia", "selecao", "corpus"), default="relevancia",
    )
    parser.add_argument("--reserva-resposta", type=int, default=512)
    parser.add_argument("--reserva-seguranca", type=int, default=64)
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--modelo", default="gpt-4-turbo")
    parser.add_argument("--taxa-prefill", type=float, default=2000.0)
    parser.add_argument("--taxa-decode", type=float, default=60.0)
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument(
        "--truncar-ultimo", action="store_true",
        help="Trunca o último chunk que não cabe no contexto ajustado.",
    )
    parser.add_argument(
        "--janela-exportacao", type=int, default=8192,
        help="Janela usada nos payloads de chat exportados.",
    )
    parser.add_argument(
        "--estrategia-exportacao", choices=ESTRATEGIAS, default="ajustado",
    )
    parser.add_argument("--sem-graficos", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Executa a Etapa 5 completa."""
    argumentos = construir_parser().parse_args(argv)
    inicio = time.perf_counter()

    dados_chunks = carregar_json(argumentos.chunks)
    instancias = carregar_json(argumentos.instancias)
    selecoes = {
        "guloso": carregar_json(argumentos.selecao_gulosa),
        "pd": carregar_json(argumentos.selecao_pd),
    }
    chunks = dados_chunks.get("chunks", [])
    chunks_map = {c["id_chunk"]: c for c in chunks}
    if len(chunks_map) != len(chunks):
        raise ValueError("IDs de chunk duplicados em chunks_tokenizados.json.")
    consulta = instancias["metadados"]["consulta"]
    encoding = tiktoken.get_encoding(argumentos.encoding)

    validacao_w_i = verificar_w_i(chunks, encoding)
    tokens_fixos = medir_tokens_fixos(consulta, encoding)
    termos_consulta = carregar_termos_consulta(consulta)

    benchmark = benchmark_selecao(instancias, selecoes, argumentos.repeticoes)
    linhas = executar_matriz(
        selecoes=selecoes,
        chunks_map=chunks_map,
        consulta=consulta,
        encoding=encoding,
        janelas=argumentos.janelas,
        estrategias=list(argumentos.estrategias),
        opcoes_dedupe=[True, False],
        ordem=argumentos.ordem,
        tokens_fixos=tokens_fixos,
        reserva_resposta=argumentos.reserva_resposta,
        reserva_seguranca=argumentos.reserva_seguranca,
        truncar_ultimo=argumentos.truncar_ultimo,
        termos_consulta=termos_consulta,
        repeticoes=argumentos.repeticoes,
        taxa_prefill=argumentos.taxa_prefill,
        taxa_decode=argumentos.taxa_decode,
    )

    contextos = exportar_contextos(
        selecoes=selecoes,
        chunks_map=chunks_map,
        consulta=consulta,
        encoding=encoding,
        tokens_fixos=tokens_fixos,
        janela=argumentos.janela_exportacao,
        estrategia=argumentos.estrategia_exportacao,
        deduplicar=True,
        ordem=argumentos.ordem,
        reserva_resposta=argumentos.reserva_resposta,
        reserva_seguranca=argumentos.reserva_seguranca,
        truncar_ultimo=argumentos.truncar_ultimo,
        termos_consulta=termos_consulta,
        modelo=argumentos.modelo,
    )

    resumo = resumir_por_orcamento(linhas, argumentos.janela_exportacao)
    comparacoes = comparar_metodos(resumo)
    relatorios_selecao = {
        seletor: carregar_json(caminho).get("tempos_segundos", {})
        for seletor, caminho in CAMINHOS_RELATORIO_SELECAO.items()
        if caminho.exists()
    }

    status_git = git("status", "--porcelain")
    metadados = {
        "etapa": "av2_5_contexto_llm",
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "consulta": consulta,
        "tokenizer": {
            "biblioteca": "tiktoken",
            "versao": version("tiktoken"),
            "encoding": encoding.name,
            "metodo": "encode_ordinary",
        },
        "modelo_referencia": argumentos.modelo,
        "chamada_llm_realizada": False,
        "janelas_llm": argumentos.janelas,
        "estrategias": argumentos.estrategias,
        "deduplicacao": [True, False],
        "ordem": argumentos.ordem,
        "reservas": {
            "resposta": argumentos.reserva_resposta,
            "seguranca": argumentos.reserva_seguranca,
            "tokens_fixos_medidos": tokens_fixos,
        },
        "entradas": {
            "chunks": {"arquivo": str(argumentos.chunks), "sha256": sha256_arquivo(argumentos.chunks)},
            "instancias": {"arquivo": str(argumentos.instancias), "sha256": sha256_arquivo(argumentos.instancias)},
            "selecao_gulosa": {"arquivo": str(argumentos.selecao_gulosa), "sha256": sha256_arquivo(argumentos.selecao_gulosa)},
            "selecao_pd": {"arquivo": str(argumentos.selecao_pd), "sha256": sha256_arquivo(argumentos.selecao_pd)},
        },
        "versionamento": {
            "commit_execucao": git("rev-parse", "HEAD"),
            "arvore_suja_antes_gravar": None if status_git is None else bool(status_git),
        },
        "observacao": (
            "Nenhuma chamada a LLM foi realizada. Os payloads são compatíveis "
            "com a API de chat e não incluem credenciais."
        ),
    }
    relatorio = {
        "metadados": metadados,
        "validacao_w_i": validacao_w_i,
        "benchmark_selecao": benchmark,
        "tempos_selecao_reportados": relatorios_selecao,
        "resumo_por_orcamento": resumo,
        "comparacao_metodos": comparacoes,
        "matriz": {
            "total_execucoes": len(linhas),
            "janelas": argumentos.janelas,
            "estrategias": argumentos.estrategias,
            "deduplicacao": [True, False],
            "repeticoes_por_celula": argumentos.repeticoes,
        },
        "contextos_exportados": {
            "arquivo": str(argumentos.saida / "contextos.json"),
            "janela": argumentos.janela_exportacao,
            "estrategia": argumentos.estrategia_exportacao,
            "deduplicar": True,
            "ordem": argumentos.ordem,
        },
        "ambiente": registrar_ambiente(),
        "tempo_total_execucao_segundos": round(time.perf_counter() - inicio, 4),
    }

    salvar_json(argumentos.saida / "contextos.json", contextos)
    salvar_csv(argumentos.saida / "tabela_contexto_llm.csv", linhas)
    salvar_json(argumentos.relatorio, relatorio)

    exemplo = next(
        (
            linha
            for linha in linhas
            if linha["seletor"] == "pd"
            and linha["W"] == max(item["W"] for item in linhas)
            and linha["janela_llm"] == argumentos.janela_exportacao
            and linha["estrategia"] == argumentos.estrategia_exportacao
            and linha["deduplicar"] is True
        ),
        None,
    )
    if exemplo is not None:
        resultado_exemplo = montar_cenario(
            seletor="pd",
            cenario_selecao=selecoes["pd"]["cenarios"][f"W_{exemplo['W']}"],
            chunks_map=chunks_map,
            consulta=consulta,
            janela=argumentos.janela_exportacao,
            estrategia=argumentos.estrategia_exportacao,
            deduplicar=True,
            ordem=argumentos.ordem,
            encoding=encoding,
            tokens_fixos=tokens_fixos,
            reserva_resposta=argumentos.reserva_resposta,
            reserva_seguranca=argumentos.reserva_seguranca,
            truncar_ultimo=argumentos.truncar_ultimo,
            termos_consulta=termos_consulta,
        )
        salvar_prompt_exemplo(argumentos.saida / "prompt_exemplo.md", resultado_exemplo)

    if not argumentos.sem_graficos:
        graficos = gerar_graficos(linhas, argumentos.saida)
        if graficos:
            print("Gráficos gerados:", *graficos, sep="\n  ")

    print("-" * 78)
    print(f"Consulta: {consulta}")
    print(f"Chunks válidos: {validacao_w_i['total_chunks']} | "
          f"tokens individuais: {validacao_w_i['tokens_individuais_total']}")
    print(f"Tokens fixos do prompt: {tokens_fixos} | "
          f"resposta: {argumentos.reserva_resposta} | segurança: {argumentos.reserva_seguranca}")
    print(f"Execuções da matriz: {len(linhas)}")
    print("Resumo por W (janela de exportação, integral, dedupe):")
    for item in resumo:
        print(f"  {item['seletor']:>6} W={item['W']:>4} | "
              f"prompt={item['tokens_prompt']:>5} | overhead={item['overhead_prompt']:>4} | "
              f"relevância={item['relevancia_incluida']:.4f} | "
              f"rel/1k={item['relevancia_por_1000_tokens_prompt']:.2f} | "
              f"folga={item['folga_llm']}")
    print(f"Artefatos em: {argumentos.saida}")
    print(f"Relatório: {argumentos.relatorio}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
