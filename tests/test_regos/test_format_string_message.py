import pytest
from datetime import datetime
from regos.format_string_message import format_partner_balance  # change to real module path


class DummyTranslator:
    """Mock translator to simulate translator_service.get(key, lang)."""
    def __init__(self):
        self.data = {
            "partner_document_type1": {"ru": "Приход", "en": "Receipt", "uz": "Kirim"},
            "document_code": {"ru": "Документ", "en": "Document", "uz": "Hujjat"},
            "exchange_rate": {"ru": "Курс", "en": "Exchange rate", "uz": "Kurs"},
            "debit": {"ru": "Приход", "en": "In", "uz": "Kirim"},
            "credit": {"ru": "Расход", "en": "Out", "uz": "Chiqim"},
            "remainder": {"ru": "Остаток", "en": "Remainder", "uz": "Qoldiq"},
            "current": {"ru": "текущий", "en": "current", "uz": "joriy"},
            "date": {"ru": "Дата", "en": "Date", "uz": "Sana"},
            "no_data": {"ru": "Нет данных", "en": "No data", "uz": "Ma'lumot yo'q"},
        }

    def get(self, key, lang):
        return self.data.get(key, {}).get(lang, key)


@pytest.fixture
def sample_data():
    """Fixture mimicking RegosReports().partner_balance_report() output."""
    now = int(datetime.now().timestamp())
    return [
        {
            "firm": {"name": "Regos Test LLC"},
            "document_type": {"id": 1, "name": "Receipt"},
            "document_code": "D001",
            "currency": {"name": "USD", "exchange_rate": 1.25},
            "start_amount": 100,
            "debit": 50,
            "credit": 0,
            "date": now - 1000,
        },
        {
            "firm": {"name": "Regos Test LLC"},
            "document_type": {"id": 1, "name": "Receipt"},
            "document_code": "D002",
            "currency": {"name": "USD", "exchange_rate": 1.25},
            "start_amount": 150,
            "debit": 0,
            "credit": 20,
            "date": now,
        },
    ]


def test_format_partner_balance_basic(sample_data):
    translator = DummyTranslator()
    messages = format_partner_balance(sample_data, lang="ru", translator=translator)

    # ✅ Expect one message per currency
    assert isinstance(messages, list)
    assert len(messages) == 1

    text = messages[0]

    # ✅ Should contain firm, currency, and known keywords
    assert "Regos Test LLC" in text
    assert "USD" in text
    assert "📄" in text
    assert "📊" in text
    assert "Дата" in text
    assert "текущий" in text  # because last operation marked as current

    # ✅ Should include formatted remainder
    assert "150.00" in text or "170.00" in text


def test_format_partner_balance_empty():
    translator = DummyTranslator()
    result = format_partner_balance([], lang="ru", translator=translator)
    assert result == ["Нет данных"]


def test_format_partner_balance_multiple_currencies(sample_data):
    """Ensure separate messages are created per currency."""
    translator = DummyTranslator()

    # Clone data and change currency for second item
    data = sample_data + [
        dict(sample_data[0], currency={"name": "EUR", "exchange_rate": 1.1}),
    ]

    messages = format_partner_balance(data, lang="ru", translator=translator)
    assert len(messages) == 2
    assert any("USD" in m for m in messages)
    assert any("EUR" in m for m in messages)
