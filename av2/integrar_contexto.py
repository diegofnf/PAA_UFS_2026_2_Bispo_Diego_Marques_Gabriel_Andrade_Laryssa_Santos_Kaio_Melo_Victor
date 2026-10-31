"""Etapa 5 — Complexidade e integração IA.

Responsável: Victor Melo.

Ponto de entrada oficial proposto pela atividade. A implementação detalhada
fica em `av2/1_scripts/montar_contexto_llm.py`, reutilizada pelos testes e pelo
notebook. Este arquivo existe para que o comando documentado na atividade seja:

    python av2/integrar_contexto.py

Ele aceita os mesmos argumentos do implementador (`--janelas`, `--repeticoes`,
`--modelo`, `--encoding`, etc.) e grava os artefatos em `av2/7_contexto_llm/` e
`av2/5_resultados/relatorio_contexto_llm.json`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


IMPLEMENTACAO = Path(__file__).resolve().parent / "1_scripts" / "montar_contexto_llm.py"


def _carregar_implementacao():
    """Importa o módulo implementador sem executar o `main` dele."""
    especificacao = importlib.util.spec_from_file_location(
        "etapa5_contexto_llm", IMPLEMENTACAO
    )
    if especificacao is None or especificacao.loader is None:
        raise ImportError(f"Não foi possível carregar {IMPLEMENTACAO}")
    modulo = importlib.util.module_from_spec(especificacao)
    sys.modules[especificacao.name] = modulo
    especificacao.loader.exec_module(modulo)
    return modulo


if __name__ == "__main__":
    sys.argv[0] = str(Path(__file__).resolve())
    raise SystemExit(_carregar_implementacao().main())
