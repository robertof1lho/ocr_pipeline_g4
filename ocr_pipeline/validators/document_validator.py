import re
from datetime import date


def validate_cpf(cpf: str) -> bool:
    """Valida CPF pelo dígito verificador."""
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    for i in range(2):
        total = sum(int(digits[j]) * (10 + i - j) for j in range(9 + i))
        expected = (total * 10 % 11) % 10
        if int(digits[9 + i]) != expected:
            return False
    return True


def validate_cnpj(cnpj: str) -> bool:
    """Valida CNPJ pelo dígito verificador."""
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6] + weights1
    for i, weights in enumerate([weights1, weights2]):
        total = sum(int(digits[j]) * weights[j] for j in range(12 + i))
        remainder = total % 11
        expected = 0 if remainder < 2 else 11 - remainder
        if int(digits[12 + i]) != expected:
            return False
    return True


def validate_cep_format(cep: str) -> bool:
    return bool(re.fullmatch(r"\d{5}-?\d{3}", cep.strip()))


def validate_document_not_expired(expiry_date: date) -> bool:
    return expiry_date >= date.today()


def validate_cid10_format(cid: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]\d{2}(?:\.\d)?", cid.strip().upper()))
