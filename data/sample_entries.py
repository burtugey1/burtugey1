import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db, Account, JournalEntry

sample = [
    {"date": "2024-01-01", "account": "3000", "desc": "Avaus tulo", "debit": 0, "credit": 1000, "vat": 0},
    {"date": "2024-01-02", "account": "4000", "desc": "Ostopalvelu", "debit": 500, "credit": 0, "vat": 24},
    {"date": "2024-01-03", "account": "1000", "desc": "Pankkitalletus", "debit": 0, "credit": 500, "vat": 0},
]

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        for row in sample:
            acc = Account.query.filter_by(number=row['account']).first()
            if acc:
                entry = JournalEntry(date=row['date'], account_id=acc.id, description=row['desc'], debit=row['debit'], credit=row['credit'], vat=row['vat'])
                db.session.add(entry)
        db.session.commit()
        print('Added sample data')
