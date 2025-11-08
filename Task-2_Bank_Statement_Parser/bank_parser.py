import os, json
from typing import Dict, Any, List, Tuple
from PIL import Image
from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
from google import genai
from dotenv import load_dotenv

from ocr_gemini import gemini_vision_ocr
from extract_and_insight import (
    call_gemini_extraction,
    call_gemini_insights,
    mask_account_number,
    validate_balances,
    retry_call,
    compute_average_daily_balance,
    detect_duplicate_transactions
)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY NOT FOUND")
else:
    print("✅ GEMINI API KEY LOADED")

client = genai.Client(api_key=api_key)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF if selectable text exists."""
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        print(f"⚠️ PDF text extraction failed: {e}")
        return ""


def load_file_to_images_or_text(file_path: str) -> Tuple[List[Image.Image], str, bool]:
    """Load file and detect if OCR is needed."""
    file_path = os.path.abspath(file_path)
    is_pdf = file_path.lower().endswith(".pdf")

    if is_pdf:
        pdf_text = extract_text_from_pdf(file_path)
        if pdf_text and len(pdf_text.split()) > 10:
            print("📄 Detected selectable text in PDF — skipping OCR.")
            return [], pdf_text, False
        else:
            print("📸 No selectable text detected — using OCR on scanned PDF.")
            images = convert_from_path(file_path, dpi=300)
            return images, "", True
    else:
        img = Image.open(file_path).convert("RGB")
        return [img], "", True


def process_bank_statement(file_path: str, test_mode: bool = False) -> Dict[str, Any]:
    """Process bank statement: OCR → Extraction → Insights."""
    if test_mode:
        return {
            "fields": {
                "fields": {
                    "bank_name": "State Bank of India",
                    "account_holder_name": "Mr. HEMANT S SHARMA",
                    "account_number_masked": "********9272",
                    "statement_month": "2025-09",
                    "account_type": "Savings",
                    "currency": "INR"
                },
                "summary": {
                    "opening_balance": 42000.00,
                    "closing_balance": 38500.00,
                    "total_credits": 30000.00,
                    "total_debits": 33500.00,
                    "average_daily_balance": 40000.50,
                    "overdraft_count": 0,
                    "nsf_count": 0
                },
                "transactions": [
                    {
                        "date": "2025-09-01",
                        "description": "SALARY CREDIT HDFC BANK",
                        "amount": 30000.00,
                        "balance": 72000.00,
                        "category": "CREDIT"
                    },
                    {
                        "date": "2025-09-10",
                        "description": "ATM CASH WITHDRAWAL – SBI MUMBAI",
                        "amount": -33500.00,
                        "balance": 38500.00,
                        "category": "ATM"
                    }
                ]
            },
            "insights": [
                "Salary of ₹30,000 credited on 1 Sep.",
                "Single ATM withdrawal of ₹33,500 detected.",
                "Closing balance stands at ₹38,500 with no overdrafts.",
                "Healthy cash flow pattern for this month."
            ],
            "quality": {
                "mode": "test",
                "text_source": "Sample Data",
                "warnings": []
            }
        }


    images, pdf_text, needs_ocr = load_file_to_images_or_text(file_path)

    if needs_ocr:
        text, ocr_meta = gemini_vision_ocr(images, client)
        text_source = "OCR (Gemini Vision)"
    else:
        text, ocr_meta = pdf_text, {"pages": [{"page": 1, "source": "PDF text", "rotation_applied": False}]}
        text_source = "PDF Extracted Text"

    print(f"🔍 Using text source: {text_source}")

    try:
        parsed = retry_call(lambda: call_gemini_extraction(text, client))
    except Exception as e:
        return {"error": f"Extraction failed: {e}"}

    if "accounts" in parsed:
        parsed = parsed["accounts"][0]

    summary = parsed.get("summary", {})
    transactions = parsed.get("transactions", [])

    if not summary.get("average_daily_balance"):
        summary["average_daily_balance"] = compute_average_daily_balance(
            transactions, summary.get("opening_balance") or 0
        )

    acct = parsed["fields"].get("account_number_masked")
    parsed["fields"]["account_number_masked"] = mask_account_number(acct)

    warnings = validate_balances(summary)
    duplicates = detect_duplicate_transactions(transactions)
    if duplicates:
        warnings.append(f"Duplicate entries detected: {duplicates} duplicates found.")

    try:
        insights = retry_call(lambda: call_gemini_insights(parsed, client))
    except Exception as e:
        insights = [f"Insight generation failed: {e}"]

    quality = {
        "pages": ocr_meta["pages"],
        "warnings": warnings,
        "text_source": text_source
    }

    return {"fields": parsed, "insights": insights, "quality": quality}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("file", help="Path to PDF or image")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    output = process_bank_statement(args.file, test_mode=args.test)
    print(json.dumps(output, indent=2, ensure_ascii=False))
