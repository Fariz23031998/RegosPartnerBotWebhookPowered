import asyncio
from datetime import datetime
from typing import List, Dict, Any, Tuple

from core.conf import TEST_INTEGRATION_TOKEN
from format_messages.partner_balance import regos_reports


def format_number(value: float) -> str:
    """Format number with thousand separators."""
    return f"{value:,.2f}".replace(",", " ")


def format_date(timestamp: int) -> str:
    """Convert Unix timestamp to readable date."""
    return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")


def generate_telegram_messages(
        data: Dict[str, Any],
        cost_or_price: str = "cost"
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Generate list of Telegram messages for documents and operations.

    Args:
        data: Dictionary containing 'documents' and 'operations' keys
        cost_or_price: Either "cost" or "price" to determine which value to use

    Returns:
        Tuple of (list of messages, total dictionary)
    """
    if cost_or_price not in ["cost", "price"]:
        raise ValueError("cost_or_price must be either 'cost' or 'price'")

    messages = []
    total_operations = 0
    grand_total = 0.0

    documents = data.get("documents", [])
    operations = data.get("operations", [])

    # Group operations by document_id
    ops_by_doc = {}
    for op in operations:
        doc_id = op["document_id"]
        if doc_id not in ops_by_doc:
            ops_by_doc[doc_id] = []
        ops_by_doc[doc_id].append(op)

    # Process each document
    for doc in documents:
        doc_id = doc["id"]
        doc_operations = ops_by_doc.get(doc_id, [])

        if not doc_operations:
            continue

        # Build document header
        header = f"<b>📄 Документ: {doc['code']}</b>\n"
        header += f"<b>Склад:</b> {doc['stock']['name']}\n"
        header += f"<b>Фирма:</b> {doc['stock']['firm']['name']}\n"
        header += f"<b>Дата:</b> {format_date(doc['date'])}\n"
        header += f"<b>Валюта:</b> {doc['currency']['name']}"

        # Add exchange rate if not 1
        if doc['currency']['exchange_rate'] != 1.0:
            header += f" (курс: {doc['currency']['exchange_rate']})"

        header += "\n\n"

        # Build operations list
        current_message = header
        doc_total = 0.0

        for idx, op in enumerate(doc_operations, 1):
            item = op["item"]
            quantity = op["quantity"]

            # Get cost or price based on parameter
            unit_value = op.get(cost_or_price, 0.0)
            total_value = quantity * unit_value

            doc_total += total_value
            total_operations += 1

            # Build operation line
            # Format name with code and articul
            item_header = f"{item['name']} ({item['code']}"
            if item.get('articul'):
                item_header += f", art: {item['articul']}"
            item_header += ")"

            op_line = f"<b>{idx}. {item_header}</b>\n"
            op_line += f"   {format_number(quantity)} x {format_number(unit_value)} = {format_number(total_value)}\n\n"

            # Check if adding this operation exceeds limit
            if len(current_message + op_line) > 2048:
                # Save current message and start new one
                messages.append(current_message.rstrip())
                current_message = header + op_line
            else:
                current_message += op_line

        # Add document total
        doc_footer = f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        doc_footer += f"<b>Итого по документу: {format_number(doc_total)}</b>\n\n"

        # Check if footer fits
        if len(current_message + doc_footer) > 2048:
            messages.append(current_message.rstrip())
            current_message = header + doc_footer
        else:
            current_message += doc_footer

        # Add current message to list
        messages.append(current_message.rstrip())
        grand_total += doc_total

    # Create final summary message
    summary = f"<b>📊 ОБЩИЙ ИТОГ</b>\n\n"
    summary += f"<b>Документов:</b> {len(documents)}\n"
    summary += f"<b>Операций:</b> {total_operations}\n"
    summary += f"<b>Общая сумма:</b> {format_number(grand_total)}\n"

    messages.append(summary)

    # Prepare total dictionary
    total_dict = {
        "operations_count": total_operations,
        "total": grand_total
    }

    return messages, total_dict


# Example usage
if __name__ == "__main__":
    # Sample data structure
    data = asyncio.run(
        regos_reports.get_partner_stock_operations(
            token=TEST_INTEGRATION_TOKEN,
            partner_id=6,
            start_time="01.01.2025 00:00:00",
            end_time="12.11.2025 00:00:00",
            operation_type="purchase"
        )
    )

    # Generate messages using cost
    messages_cost, total_cost = generate_telegram_messages(data, "cost")

    print("Messages with COST:")
    for i, msg in enumerate(messages_cost, 1):
        print(f"\n--- Message {i} (length: {len(msg)}) ---")
        print(msg)

    print(f"\n\nTotal: {total_cost}")

    # Generate messages using price
    messages_price, total_price = generate_telegram_messages(data, "price")

    print("\n\nMessages with PRICE:")
    for i, msg in enumerate(messages_price, 1):
        print(f"\n--- Message {i} (length: {len(msg)}) ---")
        print(msg)

    print(f"\n\nTotal: {total_price}")