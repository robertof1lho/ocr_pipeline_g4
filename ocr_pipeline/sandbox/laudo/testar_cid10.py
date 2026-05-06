"""
Testa a validação de CID-10 contra o Anexo da Portaria 01/2024 (local).

Uso:
    python ocr_pipeline/sandbox/laudo/testar_cid10.py --cid G35
    python ocr_pipeline/sandbox/laudo/testar_cid10.py --cid G35 G20 F71
    python ocr_pipeline/sandbox/laudo/testar_cid10.py --listar
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from ocr_pipeline.validators.medical_validator import MedicalValidator


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida CID-10 contra Portaria 01/2024")
    parser.add_argument("--cid", nargs="+", help="Código(s) CID-10 a validar (ex: G35 H54)")
    parser.add_argument("--listar", action="store_true", help="Lista todos os CIDs válidos cadastrados")
    args = parser.parse_args()

    validator = MedicalValidator()

    if args.listar:
        cids = {k: v for k, v in validator._cids.items() if not k.startswith("_")}
        print(f"\n{len(cids)} CID(s) cadastrado(s) em cids_validos.json:\n")
        for code, info in sorted(cids.items()):
            acomp = "c/ acompanhante" if info.get("acompanhante") else "sem acompanhante"
            print(f"  {code:8} — {info['nome']} ({acomp})")
        return

    if not args.cid:
        parser.print_help()
        sys.exit(1)

    print()
    for cid in args.cid:
        resultado = validator.validate_cid10(cid)
        status = "✓ VÁLIDO" if resultado["valid"] else "✗ INVÁLIDO"
        print(f"{cid:10} {status}")
        if resultado["valid"]:
            print(f"           Doença     : {resultado['disease_name']}")
            print(f"           Acompanhante: {'Sim' if resultado['requires_companion'] else 'Não'}")
            validade = resultado["validity_years"]
            print(f"           Validade   : {'Permanente' if validade is None else f'{validade} anos'}")
        print()


if __name__ == "__main__":
    main()
