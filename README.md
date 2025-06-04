# Finnish Bookkeeping Demo

This repository contains a minimal web-based bookkeeping application (Kirjanpito) for Finnish SMEs. It is built with **Flask** and **SQLite** for easy deployment.

Features:

- Upload receipts (PDF or image) with OCR using `pytesseract`.
- Import bank statement rows from CSV.
- Match receipts to bank rows.
- Store journal entries with a built-in Finnish chart of accounts.
- Generate income statement (Tuloslaskelma) and balance sheet (Tase).
- Export all entries to CSV.

## Running

Install Python dependencies and Tesseract OCR:

```bash
pip install -r requirements.txt
sudo apt-get install -y tesseract-ocr
```

Start the application:

```bash
python app.py
```

Optionally load sample data:

```bash
python data/sample_entries.py
```

The app will be available at `http://localhost:5000`.

## Stack choice

- **Flask** is lightweight and widely used, making deployment on any basic Python environment simple.
- **SQLite** requires no setup and is adequate for small businesses.
- **pytesseract** integrates well for Finnish OCR.

These choices minimize infrastructure requirements while covering Finnish accounting needs.
