"""Executa o notebook AV2 inteiro em um kernel real e salva a evidência."""

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    notebook = nbformat.read(raiz / "av2/orquestrador_av2.ipynb", as_version=4)
    nbformat.validate(notebook)
    NotebookClient(notebook, timeout=180, kernel_name="python3",
                   resources={"metadata": {"path": str(raiz)}}).execute()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, args.saida)
    print(f"Notebook executado sem erros: {args.saida}")


if __name__ == "__main__":
    main()
