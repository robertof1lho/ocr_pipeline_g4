"""
Testa a validação de CRM diretamente via portal CFM.

Uso:
    python ocr_pipeline/sandbox/laudo/testar_crm.py --crm 12345 --uf SP
    python ocr_pipeline/sandbox/laudo/testar_crm.py --crm 12345 --uf SP --nome "João Silva"
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

from ocr_pipeline.validators.medical_validator import MedicalValidator


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida CRM via portal CFM")
    parser.add_argument("--crm", required=True, help="Número do CRM")
    parser.add_argument("--uf", default="SP", help="UF do CRM (ex: SP, RJ)")
    parser.add_argument("--nome", default="", help="Nome do médico (opcional, refina a busca)")
    args = parser.parse_args()

    print(f"\nValidando CRM {args.crm}/{args.uf}...")
    print("(Aguarde — Playwright abre o browser e resolve o reCAPTCHA)\n")

    validator = MedicalValidator()
    resultado = validator.validate_crm(args.crm, args.uf)

    print("=" * 50)
    print("RESULTADO:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print("=" * 50)

    if resultado["valid"]:
        sit = resultado["situation"]
        print(f"\n✓ Médico encontrado: {resultado['doctor_name']}")
        print(f"  Especialidade : {resultado['specialty']}")
        print(f"  Situação      : {sit.upper()}")
        if sit == "inativo":
            print("  ⚠ CRM inativo — laudo pode ser rejeitado")
    else:
        print("\n✗ CRM não encontrado ou inválido")


if __name__ == "__main__":
    main()
