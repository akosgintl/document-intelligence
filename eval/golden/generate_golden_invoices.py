#!/usr/bin/env python3
"""Regenerate this repo's committed golden invoice images.

Each golden example's `expected.json` Field values must match what's actually printed on its
`submission.png` — re-run this after changing an invoice's data below:

    uv run python eval/golden/generate_golden_invoices.py
"""

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

GOLDEN_DIR = Path(__file__).parent

INVOICES: dict[str, dict[str, Any]] = {
    "invoice/basic": {
        "invoiceNumber": "INV-2026-0417",
        "invoiceDate": "2026-07-01",
        "vendorName": "Acme Robotics Supply Co.",
        "billTo": "Document Intelligence Test Harness",
        "lineItems": [("Widget A", 10, 25.00), ("Widget B", 5, 25.00)],
    },
    "invoice/high_value": {
        "invoiceNumber": "INV-2026-1183",
        "invoiceDate": "2026-03-14",
        "vendorName": "Northwind Industrial Parts",
        "billTo": "Document Intelligence Test Harness",
        "lineItems": [
            ("Servo Motor", 4, 450.00),
            ("Control Board", 8, 120.00),
            ("Cabling Kit", 20, 15.50),
        ],
    },
}


def _total(invoice: dict[str, Any]) -> float:
    return sum(qty * price for _, qty, price in invoice["lineItems"])


def render(invoice: dict[str, Any]) -> Image.Image:
    width, height = 850, 1100
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.load_default(size=36)
    label_font = ImageFont.load_default(size=20)
    body_font = ImageFont.load_default(size=18)

    y = 60
    draw.text((60, y), "INVOICE", font=title_font, fill="black")
    y += 70

    fields = [
        ("Invoice Number", invoice["invoiceNumber"]),
        ("Invoice Date", invoice["invoiceDate"]),
        ("Vendor", invoice["vendorName"]),
        ("Bill To", invoice["billTo"]),
    ]
    for label, value in fields:
        draw.text((60, y), f"{label}:", font=label_font, fill="black")
        draw.text((260, y), value, font=body_font, fill="black")
        y += 36

    y += 20
    draw.line((60, y, width - 60, y), fill="black", width=1)
    y += 20
    draw.text((60, y), "Item", font=label_font, fill="black")
    draw.text((450, y), "Qty", font=label_font, fill="black")
    draw.text((550, y), "Unit Price", font=label_font, fill="black")
    draw.text((700, y), "Amount", font=label_font, fill="black")
    y += 34

    for name, qty, price in invoice["lineItems"]:
        draw.text((60, y), name, font=body_font, fill="black")
        draw.text((450, y), str(qty), font=body_font, fill="black")
        draw.text((550, y), f"${price:,.2f}", font=body_font, fill="black")
        draw.text((700, y), f"${qty * price:,.2f}", font=body_font, fill="black")
        y += 30

    y += 20
    draw.line((60, y, width - 60, y), fill="black", width=1)
    y += 20
    draw.text((550, y), "Total Amount:", font=label_font, fill="black")
    draw.text((700, y), f"${_total(invoice):,.2f}", font=label_font, fill="black")

    return image


def main() -> None:
    for relative_dir, invoice in INVOICES.items():
        out_dir = GOLDEN_DIR / relative_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        image = render(invoice)
        out_path = out_dir / "submission.png"
        image.save(out_path, "PNG")
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
