import os
import pdfplumber
import pandas as pd
import re
from dateutil import parser

# Paths
receipts_folder = r"C:\Users\jschwab\Desktop\Receipts for Practice"

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF receipt."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return ""

def extract_vendor(lines):
    """Find vendor name dynamically by detecting the first non-numeric, non-date text line."""
    for line in lines:
        if not any(char.isdigit() for char in line):
            return line.strip()
    return None

def extract_amount(lines):
    """Extract total amount from receipt text using keyword detection."""
    keywords = ["total amount due", "total", "visa ending", "amount due", "grand total", "balance due", "subtotal", "amount charged", "payment amount", "final total"]
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in keywords):
            matches = re.findall(r'\$?([0-9,]+\.[0-9]{2})', line)
            if matches:
                return float(matches[-1].replace(",", ""))
            elif i + 1 < len(lines):
                matches = re.findall(r'\$?([0-9,]+\.[0-9]{2})', lines[i + 1])
                if matches:
                    return float(matches[-1].replace(",", ""))
    return None

def extract_date(lines):
    """Extract the date from receipt text using date parsing."""
    for line in lines:
        try:
            parsed_date = parser.parse(line, fuzzy=True)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None

def parse_receipt_data(text):
    """Extract date, vendor, and total amount from receipt text."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    vendor = extract_vendor(lines)
    amount = extract_amount(lines)
    date = extract_date(lines)
    
    return {"Date": date, "Vendor": vendor, "Total": amount}

def main():
    """Process receipts and display extracted data as a table."""
    receipts_data = []
    
    pdf_files = [f for f in os.listdir(receipts_folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return
    
    for filename in pdf_files:
        file_path = os.path.join(receipts_folder, filename)
        if os.path.isfile(file_path):  # Ensure it is a file
            text = extract_text_from_pdf(file_path)
            if text.strip():
                receipt_data = parse_receipt_data(text)
                receipts_data.append(receipt_data)
    
    if receipts_data:
        df = pd.DataFrame(receipts_data, columns=["Date", "Vendor", "Total"])
        print(df.to_string(index=False))  # Print table without unnecessary data
    else:
        print("No data extracted from receipts.")

if __name__ == "__main__":
    main()
