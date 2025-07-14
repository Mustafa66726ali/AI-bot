from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    from_currency = db.Column(db.String(10))
    to_currency = db.Column(db.String(10))
    amount = db.Column(db.Float)
    received_amount = db.Column(db.Float)
    status = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    method = db.Column(db.String(50))
    notes = db.Column(db.Text)

class ExchangeRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10))
    to_currency = db.Column(db.String(10))
    rate = db.Column(db.Float)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    answer = db.Column(db.Text)

class AppConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)

class SessionState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(50), unique=True, nullable=False)
    step = db.Column(db.String(50), default='start')
    data = db.Column(db.Text, default='{}')  # لتخزين بيانات مؤقتة كسلسلة JSON
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
