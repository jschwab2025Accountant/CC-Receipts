import os
import pdfplumber
import pandas as pd
import re
import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from dateutil import parser

# Streamlit App Title
st.title("Receipt Data Extractor with Tesseract OCR")

# File Uploader
uploaded_files = st.file_uploader("Upload PDF receipts", type=["pdf"], accept_multiple_files=True)

def extract_text_from_pdf(uploaded_file):
    """Extract text from an uploaded PDF receipt using pdfplumber and Tesseract OCR if needed."""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            
            if not text.strip():  # If no text found, use Tesseract OCR
                images = convert_from_bytes(uploaded_file.read())
                text = "\n".join(pytesseract.image_to_string(img) for img in images)
                
        return text
    except Exception as e:
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
            matches = re.findall(r'\$?([0-9,]+\\.[0-9]{2})', line)
            if matches:
                return float(matches[-1].replace(",", ""))
            elif i + 1 < len(lines):
                matches = re.findall(r'\$?([0-9,]+\\.[0-9]{2})', lines[i + 1])
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
    """Process uploaded receipts and display extracted data in Streamlit."""
    receipts_data = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            text = extract_text_from_pdf(uploaded_file)
            if text.strip():
                receipt_data = parse_receipt_data(text)
                receipts_data.append(receipt_data)
    
    if receipts_data:
        df = pd.DataFrame(receipts_data, columns=["Date", "Vendor", "Total"])
        st.write(df)  # Display table in Streamlit
    else:
        st.write("No data extracted from receipts.")

if __name__ == "__main__":
    main()
