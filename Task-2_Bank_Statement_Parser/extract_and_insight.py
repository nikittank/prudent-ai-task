import json, time
from datetime import datetime, timedelta
from typing import Dict, Any, List

PROMPT_EXTRACTION_FILE = "prompts/prompt_extraction.txt"
PROMPT_INSIGHTS_FILE = "prompts/prompt_insights.txt"
MODEL_TEXT = "gemini-2.5-flash"

def load_prompt_file(path: str) -> str:

    """Load text file contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_json_block(s: str) -> str:
    
    """Extract JSON block from model output."""
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or start > end:
        raise ValueError("No JSON object found in model output.")
    return s[start:end + 1]


def retry_call(func, retries=1, delay=2):
    
    """Retry wrapper for Gemini API calls."""
    for i in range(retries + 1):
        try:
            return func()
        except Exception as e:
            if i < retries:
                print(f"Retrying due to: {e}")
                time.sleep(delay)
            else:
                raise


def call_gemini_extraction(plain_text: str, client) -> Dict[str, Any]:
    
    """Extract structured data using Gemini."""
    print("USING GEMINI FOR EXTRACTION")
    prompt_schema = load_prompt_file(PROMPT_EXTRACTION_FILE)
    full_prompt = prompt_schema.replace("{{OCR_OR_PLAINTEXT}}", plain_text)
    response = retry_call(lambda: client.models.generate_content(
        model=MODEL_TEXT, contents=full_prompt))
    raw = getattr(response, "text", str(response))
    json_text = extract_json_block(raw)
    data = json.loads(json_text)
    return data


def call_gemini_insights(fields_json: Dict[str, Any], client) -> List[str]:
    
    """Generate financial insights from structured data."""
    print("USING GEMINI FOR INSIGHTS")
    prompt_template = load_prompt_file(PROMPT_INSIGHTS_FILE)
    payload_text = json.dumps(fields_json, indent=2)
    full_prompt = prompt_template.replace("{{EXTRACTED_JSON}}", payload_text)
    response = retry_call(lambda: client.models.generate_content(
        model=MODEL_TEXT, contents=full_prompt))
    raw = getattr(response, "text", str(response)).strip()
    if raw.startswith("["):
        return json.loads(raw)
    start, end = raw.find("["), raw.rfind("]")
    return json.loads(raw[start:end + 1]) if start != -1 else [raw]


def mask_account_number(acct: str) -> str:

    """Mask all but last 4 digits."""
    if not acct:
        return None
    digits = "".join([c for c in acct if c.isdigit()])
    if len(digits) <= 4:
        return digits
    return "*" * (len(digits) - 4) + digits[-4:]


def validate_balances(summary: dict) -> list:
    
    """Ensure opening + credits - debits ≈ closing balance."""
    warnings = []
    try:
        ob = summary.get("opening_balance") or 0
        tc = summary.get("total_credits") or 0
        td = summary.get("total_debits") or 0
        cb = summary.get("closing_balance") or 0
        calc = round(ob + tc - td, 2)
        if abs(calc - cb) > 1.0:
            warnings.append(f"Balance mismatch: opening({ob}) + credits({tc}) - debits({td}) = {calc}, but closing = {cb}.")
    except Exception as e:
        warnings.append(f"Balance validation error: {e}")
    return warnings


def detect_duplicate_transactions(transactions: list) -> int:

    """Detect and count duplicate transactions."""    
    seen, duplicates = set(), 0
    for tx in transactions:
        key = (tx.get("date"), tx.get("amount"), (tx.get("description") or "").strip().lower())
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates


def compute_average_daily_balance(transactions: list, opening_balance: float) -> float:
    
    """Compute average daily balance using transactions."""
    if not transactions:
        return opening_balance or 0.0
    txs = []
    for tx in transactions:
        try:
            txs.append((datetime.fromisoformat(tx["date"]), tx["balance"]))
        except Exception:
            continue
    if not txs:
        return opening_balance
    txs.sort(key=lambda x: x[0])
    total_days = (txs[-1][0] - txs[0][0]).days + 1
    total_balance = 0
    prev_date, prev_balance = txs[0]
    for date, balance in txs[1:]:
        days = (date - prev_date).days or 1
        total_balance += prev_balance * days
        prev_date, prev_balance = date, balance
    total_balance += prev_balance
    return round(total_balance / total_days, 2)