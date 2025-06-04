from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import csv
import io

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'data', 'bookkeeping.db')
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db = SQLAlchemy(app)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text)

class BankRow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    matched_receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'))
    matched_receipt = db.relationship('Receipt', foreign_keys=[matched_receipt_id])

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    description = db.Column(db.String(200))
    debit = db.Column(db.Float)
    credit = db.Column(db.Float)
    vat = db.Column(db.Float)

def setup():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
        if Account.query.count() == 0:
            load_chart_of_accounts()


def load_chart_of_accounts():
    import json
    path = os.path.join('data', 'tilikartta.json')
    if not os.path.exists(path):
        return
    with open(path) as f:
        accounts = json.load(f)
    for acc in accounts:
        db.session.add(Account(number=acc['number'], name=acc['name']))
    db.session.commit()

@app.route('/')
def index():
    receipts = Receipt.query.all()
    bank_rows = BankRow.query.all()
    return render_template('index.html', receipts=receipts, bank_rows=bank_rows)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        text = extract_text(path)
        receipt = Receipt(filename=filename, text=text)
        db.session.add(receipt)
        db.session.commit()
    return redirect(url_for('index'))


def extract_text(path):
    if path.lower().endswith('.pdf'):
        images = convert_from_path(path)
        text = ''
        for img in images:
            text += pytesseract.image_to_string(img, lang='fin')
        return text
    else:
        return pytesseract.image_to_string(Image.open(path), lang='fin')

@app.route('/bank_upload', methods=['POST'])
def bank_upload():
    file = request.files['file']
    if file:
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        for row in reader:
            bank_row = BankRow(date=row.get('date'), description=row.get('description'), amount=float(row.get('amount', 0)))
            db.session.add(bank_row)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/match/<int:bank_id>/<int:receipt_id>')
def match(bank_id, receipt_id):
    bank_row = BankRow.query.get(bank_id)
    bank_row.matched_receipt_id = receipt_id
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/reports')
def reports():
    entries = JournalEntry.query.all()
    accounts = {acc.id: acc for acc in Account.query.all()}
    income = {}
    balance = {}
    for e in entries:
        acc = accounts.get(e.account_id)
        if not acc:
            continue
        target = income if acc.number.startswith('3') or acc.number.startswith('4') else balance
        target.setdefault(acc.number + ' ' + acc.name, 0)
        target[acc.number + ' ' + acc.name] += (e.credit - e.debit)
    return render_template('reports.html', income=income, balance=balance)

@app.route('/export.csv')
def export_csv():
    entries = JournalEntry.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'account', 'description', 'debit', 'credit', 'vat'])
    for e in entries:
        writer.writerow([e.date, e.account_id, e.description, e.debit, e.credit, e.vat])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, attachment_filename='bookkeeping.csv')

if __name__ == '__main__':
    setup()
    app.run(debug=True)
