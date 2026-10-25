"""Independent consent and field-coverage regressions, with no sample labels."""
import pytest

from deletion_audit.authorization import authorize
from deletion_audit.state import exposed, observed_state
from test_solver import obs


@pytest.mark.parametrize("text", [
    "Hapus akun saya. Jangan hapus faktur yang wajib disimpan.",
    "Hapus akun saya, tetapi jangan hapus faktur saya.",
    "Quiero eliminar mi cuenta. No borres mis facturas.",
    "Supprimer mon compte. Ne supprimez pas mes factures.",
    "Excluir minha conta. Nao apague minhas faturas.",
    "Please erase my account; don't delete retained invoices.",
    "アカウントを削除してください。請求書は削除しないでください。",
    "계정을 삭제해 주세요. 청구서는 삭제하지 마세요.",
    "删除我的账户。不要删除发票。",
    "Jangan hapus faktur dan hapus akun saya.",
    "No borres mis facturas y elimina mi cuenta.",
    "Ne supprimez pas mes factures et supprimer mon compte.",
    "Nao apague minhas faturas e exclua minha conta.",
    "Do not delete invoices and erase my account.",
])
def test_account_deletion_with_document_preservation(text):
    assert authorize(text).authorized is True


@pytest.mark.parametrize("text", [
    "Jangan hapus akun saya.", "No borres mi cuenta.",
    "Please correct my email address.", "Please send a copy of my personal data.",
    "Stop promotional messages only; keep my account active.",
    "Please remove my data from your mailing list only.",
    "Do not delete my account. Please delete my invoices.",
    "不要删除我的账户。", "Ne supprimez pas mon compte.",
])
def test_no_deletion_consent(text):
    assert authorize(text).authorized is False


def test_conflicting_account_consent_is_unknown():
    assert authorize("Delete my account. Do not delete my account.").authorized is None
    assert authorize("Delete my account. Keep my account active.").authorized is None
    assert authorize("Supprimer mon compte et ne supprimez pas mon compte.").authorized is None


@pytest.mark.parametrize("fields", [{}, {"email": None}, {"name": None, "email": None},
    {"email": None, "phone": None, "email_hash": None}])
def test_partial_fields_are_not_redaction_proof(fields):
    assert exposed(fields) is None
    assert observed_state(obs("ACCOUNT_TOMBSTONE", fields=fields or {"other": None})) is None


def test_exhaustive_nulls_allow_tombstone_with_stable_reference():
    fields = dict(name=None, email=None, phone=None, email_hash=None, user_id="user_fixture")
    assert observed_state(obs("ACCOUNT_TOMBSTONE", fields=fields)) == "REDACTED"
    assert observed_state(obs("ANALYTICS_PROFILE", fields=fields)) == "IDENTIFIABLE"


@pytest.mark.parametrize("link", ["user_id", "customer_reference", "subject_reference", "subject_ref"])
def test_stable_link_overrides_clean_certificate(link):
    fields = {"direct_identifiers": "0", "result": "ANONYMIZED", link: "user_fixture"}
    assert observed_state(obs("ANALYTICS_PROFILE", fields=fields)) == "IDENTIFIABLE"


def test_literal_pii_overrides_redaction_certificate():
    assert observed_state(obs("SUPPORT_MESSAGE", fields={"result": "REDACTED",
        "requester_email": "fiction@example.test"})) == "IDENTIFIABLE"


def test_direct_certificate_and_category_schema_coverage():
    assert observed_state(obs("ANALYTICS_PROFILE", fields={"direct_identifiers": "0"})) == "ANONYMIZED"
    assert observed_state(obs("ANALYTICS_PROFILE", fields={"customer_reference": None,
        "email": None, "phone": None, "email_hash": None})) == "ANONYMIZED"
    assert observed_state(obs("SUPPORT_MESSAGE", fields={"requester_name": None,
        "requester_email": None, "requester_phone": None})) == "REDACTED"
