#!/usr/bin/env python3
"""Generate a sample invoice (PNG + PDF) for scripts/manual_test.py.

The outputs are committed under scripts/samples/, so this only needs to be
re-run if you want different sample data:

    uv run python scripts/generate_sample_invoice.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent / "samples"

INVOICE = {
    "invoiceNumber": "INV-2026-0417",
    "invoiceDate": "2026-07-01",
    "vendorName": "Acme Robotics Supply Co.",
    "billTo": "Document Intelligence Test Harness",
    "lineItems": [
        ("Widget A", 10, 25.00),
        ("Widget B", 5, 25.00),
    ],
}


def _total(invoice: dict) -> float:
    return sum(qty * price for _, qty, price in invoice["lineItems"])


def render() -> Image.Image:
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
        ("Invoice Number", INVOICE["invoiceNumber"]),
        ("Invoice Date", INVOICE["invoiceDate"]),
        ("Vendor", INVOICE["vendorName"]),
        ("Bill To", INVOICE["billTo"]),
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

    for name, qty, price in INVOICE["lineItems"]:
        draw.text((60, y), name, font=body_font, fill="black")
        draw.text((450, y), str(qty), font=body_font, fill="black")
        draw.text((550, y), f"${price:,.2f}", font=body_font, fill="black")
        draw.text((700, y), f"${qty * price:,.2f}", font=body_font, fill="black")
        y += 30

    y += 20
    draw.line((60, y, width - 60, y), fill="black", width=1)
    y += 20
    draw.text((550, y), "Total Amount:", font=label_font, fill="black")
    draw.text((700, y), f"${_total(INVOICE):,.2f}", font=label_font, fill="black")

    return image


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    image = render()
    image.save(OUT_DIR / "invoice.png", "PNG")
    image.save(OUT_DIR / "invoice.pdf", "PDF")
    print(f"wrote {OUT_DIR / 'invoice.png'}")
    print(f"wrote {OUT_DIR / 'invoice.pdf'}")


if __name__ == "__main__":
    main()
