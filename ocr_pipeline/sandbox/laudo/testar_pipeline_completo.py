"""
Testa o pipeline completo de extração e validação de um Laudo Médico PCD.

Uso:
    python ocr_pipeline/sandbox/laudo/testar_pipeline_completo.py imagens/laudo.jpg
    python ocr_pipeline/sandbox/laudo/testar_pipeline_completo.py imagens/laudo.jpg --perfil pcd
    python ocr_pipeline/sandbox/laudo/testar_pipeline_completo.py imagens/laudo.jpg --so-ocr
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from ocr_pipeline.main import process_document
from ocr_pipeline.preprocessor.image_processor import preprocess
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline completo de Laudo Médico PCD")
    parser.add_argument("imagem", help="Caminho para a imagem do laudo")
    parser.add_argument(
        "--perfil", choices=["pcd", "estudante", "idoso"], default="pcd"
    )
    parser.add_argument(
        "--so-ocr",
        action="store_true",
        help="Roda apenas pré-processamento + OCR, sem extração de campos",
    )
    args = parser.parse_args()

    # Resolve relativo ao script quando o caminho não existe no cwd
    _SCRIPT_DIR = Path(__file__).parent
    caminho = Path(args.imagem)
    if not caminho.exists():
        caminho = _SCRIPT_DIR / args.imagem
    if not caminho.exists():
        print(f"Arquivo não encontrado: {args.imagem}")
        print(f"  Tentado em: {Path(args.imagem).resolve()}")
        print(f"  Tentado em: {(_SCRIPT_DIR / args.imagem).resolve()}")
        sys.exit(1)

    if args.so_ocr:
        _modo_so_ocr(str(caminho))
        return

    print(f"\nProcessando: {caminho.name}")
    print(f"Perfil     : {args.perfil}")
    print("=" * 60)

    resultado = process_document(str(caminho), "laudo_medico", args.perfil)

    _imprimir_resultado(resultado)


def _modo_so_ocr(caminho: str) -> None:
    """Exibe apenas o texto bruto do OCR sem chamar extratores ou LLM."""
    print(f"\nModo OCR puro: {caminho}")
    print("=" * 60)
    try:
        prep = preprocess(caminho)
        print(f"Quality score: {prep['quality_score']:.2f}")
        engine = TesseractEngine()
        texto = engine.extract_text(prep["processed"], psm=6)
        print("\nTexto extraído (PSM 6):\n")
        print(texto)
        print("\n--- PSM 3 (layout automático) ---\n")
        print(engine.extract_text(prep["processed"], psm=3))
    except ValueError as exc:
        print(f"Erro: {exc}")


def _imprimir_resultado(resultado: dict) -> None:
    status = resultado["status"].upper()
    icone = {"SUCCESS": "✓", "ERROR": "✗", "MANUAL_REVIEW": "⚠"}.get(status, "?")
    print(f"\n{icone} Status: {status}\n")

    if resultado["errors"]:
        print("Erros:")
        for e in resultado["errors"]:
            print(f"  - {e}")
        print()

    if resultado["data"]:
        print("Campos extraídos:")
        for campo, valor in resultado["data"].items():
            if valor is not None:
                print(f"  {campo:<35} {valor}")
        print()

    if resultado["validations"]:
        print("Validações:")
        for validacao, val in resultado["validations"].items():
            icone_v = "✓" if val is True or (isinstance(val, dict) and val.get("aprovado")) else "✗"
            print(f"  {icone_v} {validacao}: {json.dumps(val, ensure_ascii=False)}")
        print()

    print("Texto bruto OCR (primeiros 500 chars):")
    print("-" * 60)
    print(resultado["raw_text"][:500])
    print("-" * 60)


if __name__ == "__main__":
    main()
