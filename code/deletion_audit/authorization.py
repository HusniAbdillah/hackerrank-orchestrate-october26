"""Conservative multilingual intent gate. Unknown intent is an abstention, not consent."""

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Authorization:
    authorized: bool | None
    reason: str


def _account_clauses(value: str) -> tuple[bool, bool]:
    """Bind explicit deletion/negation to its account object, across languages.

    Keeping an invoice is not a veto on deleting an account. Contradictory
    instructions about the account itself must not be resolved as consent.
    """
    clauses = re.split(r"[.!?;,\n。！？；，]|\b(?:but|however|pero|mais|mas|tetapi|namun)\b", value)
    target = re.compile(
        r"(?:delete|erase|remove|close)\s+(?:(?:my|the|this|permanently)\s+){0,4}(?:account|profile|personal data)\b|"
        r"(?:eliminar|elimina|borra|borres|elimines)\s+(?:mi\s+)?cuenta\b|"
        r"(?:supprimer|supprimez)\s+(?:(?:mon|le|votre)\s+)?compte\b|"
        r"(?:excluir|exclua|apagar|apague)\s+(?:(?:a|minha)\s+){0,2}conta\b|"
        r"(?:hapus|menghapus)\s+(?:akun|profil|data pribadi)\b|"
        r"アカウント[^。！？]{0,20}削除|계정[^。！？]{0,20}삭제|(?:删除|刪除)[^。！？]{0,8}(?:账户|帳戶)")
    negation = re.compile(
        r"\b(?:do not|don't|never|not asking|not a request|not requesting|without|"
        r"no|ne|pas|nao|jangan)\b|削除しない|삭제하지|不要|하지 마")
    positive = negative = False
    for clause in clauses:
        if re.search(r"(?:keep|leave).*(?:account|profile).*(?:active|in place|as it is)", clause):
            negative = True
        if target.search(clause):
            if negation.search(clause):
                negative = True
            else:
                positive = True
    return positive, negative


def authorize(text: str) -> Authorization:
    value = unicodedata.normalize("NFKD", text.casefold()).replace("’", "'")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = unicodedata.normalize("NFC", value)
    # An opt-out is not authorization to delete an account. A separate explicit account
    # deletion sentence takes precedence over unrelated instructions to preserve retained data.
    positive = bool(re.search(
        r"(?:delete|erase|remov\w*|clos\w*)\s+(?:(?:my|this|the|its|your|associated|personal|permanent|remaining)\s+){0,5}"
        r"(?:account|profile|personal|data)|account[- ]deletion|permanently deleted|deleting my account|"
        r"completar la eliminacion|eliminar mi cuenta|eliminacion permanente|"
        r"suppression definitive|supprimer.*compte|exclusao permanente|"
        r"アカウント.*削除|계정.*삭제|删除.*账户|hapus.*akun|"
        r"remove records linked|remove records under|remove my name and contact|"
        r"account.{0,100}(?:erased|deleted|removed)|request(?:ing)?.*deletion|"
        r"keep only the reference.*remove|"
        r"(?:verify|audit|check|inspect).*(?:account.*deleted|deletion|fully removed|profile.*gone)|"
        r"remove (?:that|the) search result|before deleting it|finish the deletion|"
        r"deleted (?:this|my|the) account|remove any remaining copy|"
        r"(?:begin|start|initiate).{0,25}deletion process", value
    ))
    negative = bool(re.search(
        r"(?:do not|don't|not asking for|not a request to|without)\s+(?:close|delete|delet\w*|erase|eras\w*|remov\w*)|"
        r"(?:do not|don't|never)\s+(?:want to\s+)?(?:delete|erase|close)|not requesting (?:account )?deletion|"
        r"(?:marketing|promotional|mailing).*(?:only|still need|still want)|"
        r"(?:keep|leave).*(?:account|profile).*(?:active|as it is|in place)|"
        r"(?:please (?:correct|replace|change)|i want to (?:correct|replace|change)).*(?:surname|email address|mobile number)|resetting the login|"
        r"no (?:elimines|eliminar|borres)|ne supprimez pas|nao (?:exclua|apague)|"
        r"削除しない|삭제하지|不要删除|jangan (?:hapus|menghapus)", value
    ))
    explicit, account_veto = _account_clauses(value)
    if explicit and account_veto:
        return Authorization(None, "Conflicting deletion and preservation instructions for the account")
    if negative:
        if not explicit or account_veto:
            return Authorization(False, "Explicit non-deletion, correction, access, or limited opt-out request")
    if positive or explicit:
        return Authorization(True, "Explicit account/data deletion or requested deletion audit")
    if re.search(r"(?:copy|download|portable|information request|what personal information|invoices for my records|correct|misspelled|continue using)", value):
        return Authorization(False, "Access, portability, correction, or continued-account-use request")
    return Authorization(None, "Intent not recognized reliably by the deterministic multilingual gate")
