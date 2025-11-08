# Task 1 - Transaction Value Extractor (Regex Capture Challenge)

## Objective

Extract all valid transaction details from a multiline text log that follow the pattern:

```
TXN:<type> | AMT:<amount> | ID:<alphanumeric>
```

Return a list of tuples in the format:

```
(txn_type, amount, txn_id)
```

where

* `txn_type` → transaction type (e.g. `CREDIT`, `DEBIT`)
* `amount` → float number, handles commas and decimals
* `txn_id` → alphanumeric transaction code

If no valid entries exist, return an empty list `[]`.

<img width="532" height="327" alt="Task1-ss" src="https://github.com/user-attachments/assets/ea9158d3-df21-46a5-ad97-33f3b7efe2cc" />




# Task 2 - Bank Statement Parser (Gemini)

## Overview

This task is a Python-based **bank statement parser** that uses **Google Gemini** (Generative AI) to read and analyze PDF or image-based bank statements.
It automatically extracts key financial details, transactions, and summary insights into a structured, easy-to-use JSON format.

The goal is to simplify financial data extraction and generate meaningful insights like spending patterns, salary detection, and average balance analysis.

---

## Key Features

* Works with both **PDFs and images**
* Detects and extracts text automatically (built-in OCR fallback using Gemini Vision)
* Outputs **structured JSON** containing account info, summaries, and transactions
* Generates **financial insights** from extracted data using Gemini
* Handles scanned or rotated documents
* Includes a **test mode** for running without real API calls
* Privacy-friendly — no files or sensitive data are stored after processing

---

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/bank-statement-parser.git
cd bank-statement-parser
```

### 2. Install dependencies

Make sure you have Python 3.9+ installed.

```bash
pip install -r requirements.txt
```

### 3. Environment setup

Create a `.env` file in the root directory and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

You can get an API key from your **Google AI Studio** account.

---

## How to Run

### 1. Command Line (CLI)

You can run the parser directly from the terminal:

```bash
python bank_parser.py "path/to/your/statement.pdf"
```

### 2. Test Mode

To simulate the output without calling the Gemini API:

```bash
python bank_parser.py "sample.pdf" --test
```

This will return a mock structured JSON output that mimics a real response (with two transactions and insights).

---

## Using `process_bank_statement()` in Your Code

You can also import and use the main function in your own project:

```python
from bank_parser import process_bank_statement

result = process_bank_statement("statement.pdf")
print(result)
```

Or run in test mode:

```python
result = process_bank_statement("sample.pdf", test_mode=True)
```

This returns a dictionary containing three main keys:

```python
{
  "fields": {...},
  "insights": [...],
  "quality": {...}
}
```

---

## Sample Output

<p align="center">
  <a href="https://github.com/user-attachments/assets/c9d1be51-3d20-49b5-9a5b-c1837081cb33">
    <img 
      src="https://github.com/user-attachments/assets/c9d1be51-3d20-49b5-9a5b-c1837081cb33" 
      alt="Bank Statement Analyzer Interface" 
      width="785" 
      style="max-width:100%; height:auto; border-radius:6px;" />
  </a>
</p>


## Test Mode

When test mode is enabled:

* The program skips all API calls.
* Returns a predefined, realistic sample JSON.
* Useful for frontend or UI testing.

---

## Known Limitations

* Complex multi-account statements may not always separate correctly.
* Very low-quality scans can affect OCR accuracy.
* Currency detection is basic (₹ / $ / € support included).
* Long statements may increase Gemini API costs.
* Requires stable internet connection for Gemini API calls.

---
