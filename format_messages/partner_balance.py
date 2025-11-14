import asyncio
from datetime import datetime
from core.conf import translator_service, TEST_INTEGRATION_TOKEN
from collections import defaultdict

from core.utils import write_json_file
from regos.reports import RegosReports


def format_partner_balance(data: list, lang: str = "ru", translator=translator_service, newest_first: bool = False) -> list[str]:
    """
    Formats partner balance data for Telegram messages (HTML).
    Creates a separate message for each currency.

    Parameters:
        data: list of dicts with document info
        lang: 'en', 'ru', 'uz'
        translator: object with translator.get(key, lang)
        newest_first: reverse order of operations
    """
    if not data:
        return [translator.get("no_data", lang)]


    # --- Group operations by currency
    currencies = {}
    for op in data:
        currency_name = op.get("currency", {}).get("name", "Unknown")
        currencies.setdefault(currency_name, []).append(op)

    messages = []

    for currency_name, operations in currencies.items():
        # Sort by date
        operations.sort(key=lambda x: x.get("date", 0), reverse=newest_first)
        last_op = operations[-1]

        text = f"💱 <b>{currency_name}</b>\n\n"

        for op in operations:
            doc_type_id = op.get("document_type", {}).get("id", "0")
            code = op.get("document_code", "—")
            curr = op.get("currency", {})
            exch = curr.get("exchange_rate", 1)
            start = op.get("start_amount", 0)
            debit = op.get("debit", 0)
            credit = op.get("credit", 0)
            date = datetime.fromtimestamp(op.get("date", 0)).strftime("%d.%m.%y %H:%M")
            remainder = start + debit - credit

            lines = [
                f"<b>{translator.get(f"partner_document_type{doc_type_id}", lang)}</b>",
                f"📄 <b>{translator.get('document_code', lang)}:</b> {code}",
            ]
            if exch != 1:
                lines.append(f"🔢 <b>{translator.get('exchange_rate', lang)}:</b> {exch:,.2f}")
            if debit != 0:
                lines.append(f"🟢 <b>{translator.get('debit', lang)}:</b> {debit:,.2f}")
            if credit != 0:
                lines.append(f"🔴 <b>{translator.get('credit', lang)}:</b> {credit:,.2f}")

            rem_label = translator.get("remainder", lang)
            if op is last_op:
                lines.append(f"📊 <b>{rem_label} ({translator.get('current', lang)}):</b> {remainder:,.2f}")
            else:
                lines.append(f"📊 <b>{rem_label}:</b> {remainder:,.2f}")

            lines.append(f"🕓 <b>{translator.get('date', lang)}:</b> {date}")
            text += "\n".join(lines) + "\n\n"

        # --- Split if message exceeds Telegram 2048-char limit
        while len(text) > 2048:
            split_idx = text.rfind("\n\n", 0, 2048)
            messages.append(text[:split_idx].strip())
            text = text[split_idx:].strip()

        messages.append(text.strip())

    return messages

def format_total(data: list, lang: str = "ru", translator=translator_service) -> list[str]:
    """
    Formats partner balance data for Telegram messages (HTML).
    Groups by document_type, then by currency.
    Each message shows totals per document_type and overall total per currency.
    """

    if not data:
        return [translator.get("no_data", lang)]

    # --- Group operations by currency
    currencies = defaultdict(list)
    for op in data:
        currency_name = op.get("currency", {}).get("name", "Unknown")
        currencies[currency_name].append(op)

    messages = []

    currency_list = []
    total_in_base_currency = 0

    for currency_name, operations in currencies.items():
        # Sort operations by date
        operations.sort(key=lambda x: x.get("date", 0))


        text = f"💱 <b>{currency_name}</b>\n\n"

        # --- Group by document_type
        doc_groups = defaultdict(list)
        for op in operations:
            doc_type_id = op.get("document_type", {}).get("id", "0")
            doc_groups[doc_type_id].append(op)

        total_currency_sum = 0

        for doc_type_id, ops in doc_groups.items():
            if not ops:
                continue

            # Calculate totals
            # For user's partner debit considers as credit and vice-versa
            total_credit = sum(o.get("debit", 0) for o in ops)
            total_debit = sum(o.get("credit", 0) for o in ops)
            total_value = total_debit - total_credit

            # Use first op's currency exchange rate
            total_currency_sum += total_value

            # Compose text for document type
            doc_type_name = translator.get(f"plural_partner_document_type{doc_type_id}", lang)
            text += (
                f"📄 <b>{doc_type_name}</b>: {total_value:,.2f}\n"
            )

        # --- Add total per currency
        text += f"💰 <b>{translator.get('currency_total', lang)}:</b> {total_currency_sum:,.2f}\n"

        # --- Add for all currency
        currency_id = operations[-1].get("currency", {}).get("id", "0")
        exchange_rate = operations[-1].get("currency", {}).get("exchange_rate", 1)
        start_amount = operations[0].get("start_amount", 0)
        currency_list.append({
            "id": currency_id,
            "name": currency_name,
            "exchange_rate": operations[-1].get("currency", {}).get("exchange_rate", 1)
        })

        total_in_base_currency += (total_currency_sum + start_amount) * exchange_rate

        # --- Split if message exceeds Telegram 2048-char limit
        while len(text) > 2048:
            split_idx = text.rfind("\n\n", 0, 2048)
            messages.append(text[:split_idx].strip())
            text = text[split_idx:].strip()

        messages.append(text.strip())

    word_total = translator.get('total', lang)
    total_message = ""
    for currency_info in currency_list:
        exchange_rate = currency_info['exchange_rate']
        total_message += f"<b>{word_total} ({currency_info['name']}):</b> {total_in_base_currency / exchange_rate:,.2f}\n"

    messages.append(total_message.strip())

    return messages

# Example usage:
from core.conf import translator_service, TEST_INTEGRATION_TOKEN
from regos.reports import RegosReports
import asyncio

regos_reports = RegosReports()


# data = asyncio.run(
#     regos_reports.partner_balance_report(
#         token=TEST_INTEGRATION_TOKEN,
#         partner_id=6,
#         firm_id=1,
#         start_time="01.01.2025 00:00:00",
#         end_time="12.11.2025 00:00:00"
#     )
# )

# Format detailed balance
# format_partner_balance_result = format_partner_balance(data=data["result"], lang="uz", translator=translator_service)
#
# for r in format_partner_balance_result:
#     print(r)


# Format totals
# format_total_result = format_total(data=data["result"], lang="uz", translator=translator_service)
# for f in format_total_result:
#     print(f)

# Format wholesale

#

