"""Generate the synthetic customs document test set.

Creates 20 fictional trade documents (commercial invoices, shipping
manifests, and short memos) plus a ground-truth JSON file with the fields a
careful human could extract from each document.

All companies, amounts, and documents are invented. No real CBP data,
no real businesses, no personal data.

Run:
    python generate_docs.py
Writes:
    data/documents.json
    data/ground_truth.json
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Five fictional shipments. Each is rendered in four document styles.
SHIPMENTS = [
    {
        "invoice_number": "INV-8841",
        "invoice_date": "2026-08-14",
        "seller": "Shenzhen Bright LED Co.",
        "buyer": "Pacific Import Group LLC",
        "currency": "USD",
        "total_amount": 18450.00,
        "hs_chapter": 85,
        "incoterm": "FOB",
        "goods": "LED panel lights, 1,200 units",
        "port": "Shenzhen",
    },
    {
        "invoice_number": "INV-2290",
        "invoice_date": "2026-09-02",
        "seller": "Hanoi Textile Export JSC",
        "buyer": "East Coast Apparel Inc",
        "currency": "USD",
        "total_amount": 6720.50,
        "hs_chapter": 61,
        "incoterm": "CIF",
        "goods": "Knitted cotton polo shirts, 3,000 units",
        "port": "Haiphong",
    },
    {
        "invoice_number": "INV-77310",
        "invoice_date": "2026-07-21",
        "seller": "Guadalajara Auto Parts SA",
        "buyer": "Midwest Motors Supply",
        "currency": "USD",
        "total_amount": 42980.75,
        "hs_chapter": 87,
        "incoterm": "DDP",
        "goods": "Brake assemblies and rotors, 640 units",
        "port": "Manzanillo",
    },
    {
        "invoice_number": "INV-5519",
        "invoice_date": "2026-08-30",
        "seller": "Gdansk Steel Works Sp. z o.o.",
        "buyer": "Atlantic Building Materials",
        "currency": "USD",
        "total_amount": 96300.00,
        "hs_chapter": 72,
        "incoterm": "FOB",
        "goods": "Hot-rolled steel coils, 210 metric tons",
        "port": "Gdansk",
    },
    {
        "invoice_number": "INV-0934",
        "invoice_date": "2026-09-11",
        "seller": "Chennai Spice Traders Pvt Ltd",
        "buyer": "Golden Gate Foods Inc",
        "currency": "USD",
        "total_amount": 3125.25,
        "hs_chapter": 9,
        "incoterm": "CFR",
        "goods": "Dried red chilies, 900 kg",
        "port": "Chennai",
    },
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def long_date(iso: str) -> str:
    year, month, day = iso.split("-")
    return f"{MONTHS[int(month) - 1]} {int(day)}, {year}"


def money(amount: float) -> str:
    return f"{amount:,.2f}"


def render_formal(s: dict) -> str:
    return (
        "COMMERCIAL INVOICE\n"
        f"Invoice Number: {s['invoice_number']}\n"
        f"Invoice Date: {s['invoice_date']}\n"
        f"Seller: {s['seller']}\n"
        f"Buyer: {s['buyer']}\n"
        f"Goods: {s['goods']}\n"
        f"HS Chapter: {s['hs_chapter']}\n"
        f"Total Amount: {s['currency']} {money(s['total_amount'])}\n"
        f"Incoterm: {s['incoterm']} {s['port']}\n"
    )


def render_email(s: dict) -> str:
    return (
        f"Hi team,\n\n"
        f"Attaching the paperwork for the latest shipment from {s['seller']}. "
        f"This is invoice {s['invoice_number']}, dated {long_date(s['invoice_date'])}, "
        f"for the {s['goods'].lower()} going to {s['buyer']}. "
        f"The total on the invoice is ${money(s['total_amount'])} and the goods "
        f"fall under HS chapter {s['hs_chapter']}. "
        f"Terms are {s['incoterm']} out of {s['port']}. "
        f"Please file the entry when you get a chance.\n\nThanks!"
    )


def render_manifest(s: dict) -> str:
    return (
        "SHIPPING MANIFEST\n"
        f"DOC {s['invoice_number']} / DT {s['invoice_date']}\n"
        f"SHIPPER: {s['seller']}\n"
        f"CONSIGNEE: {s['buyer']}\n"
        f"DESC: {s['goods']}\n"
        f"HS {s['hs_chapter']} / TERMS {s['incoterm']} {s['port']}\n"
        f"VALUE: {money(s['total_amount'])} {s['currency']}\n"
    )


def render_memo(s: dict) -> str:
    # Minimal memo: deliberately omits the HS chapter and the incoterm.
    # Ground truth for those fields is null, and a correct extraction
    # must return null instead of guessing. This is the hallucination test.
    return (
        f"Quick note on invoice {s['invoice_number']} ({s['invoice_date']}): "
        f"{s['seller']} billed {s['buyer']} {s['currency']} "
        f"{money(s['total_amount'])} for the {s['goods'].lower()}. "
        f"Full paperwork to follow."
    )


RENDERERS = [
    ("formal_invoice", render_formal, True),
    ("email", render_email, True),
    ("manifest", render_manifest, True),
    ("memo", render_memo, False),
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    documents = []
    ground_truth = {}
    for idx, shipment in enumerate(SHIPMENTS, start=1):
        for style_name, renderer, complete in RENDERERS:
            doc_id = f"doc-{idx:02d}-{style_name}"
            documents.append(
                {"doc_id": doc_id, "style": style_name, "text": renderer(shipment)}
            )
            truth = {
                "invoice_number": shipment["invoice_number"],
                "invoice_date": shipment["invoice_date"],
                "seller": shipment["seller"],
                "buyer": shipment["buyer"],
                "currency": shipment["currency"],
                "total_amount": shipment["total_amount"],
                "hs_chapter": shipment["hs_chapter"] if complete else None,
                "incoterm": shipment["incoterm"] if complete else None,
            }
            ground_truth[doc_id] = truth
    (DATA_DIR / "documents.json").write_text(
        json.dumps(documents, indent=2), encoding="utf-8"
    )
    (DATA_DIR / "ground_truth.json").write_text(
        json.dumps(ground_truth, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(documents)} documents and ground truth for each.")


if __name__ == "__main__":
    main()
