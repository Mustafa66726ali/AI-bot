from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os
from models import db, User, Transaction, ExchangeRate, FAQ, AppConfig, SessionState

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exchange.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ربط إعدادات النظام
from settings import settings_bp
app.register_blueprint(settings_bp)

db.init_app(app)
admin = Admin(app, name='لوحة إدارة متجر رييل', template_mode='bootstrap4')

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Transaction, db.session))
admin.add_view(ModelView(ExchangeRate, db.session))
admin.add_view(ModelView(FAQ, db.session))
admin.add_view(ModelView(AppConfig, db.session))

@app.route('/')
def index():
    return render_template('index.html')

from twilio_utils import build_twilio_response

import json

@app.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    from flask import request
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    phone = sender.replace('whatsapp:', '')

    # جلب أو إنشاء حالة الجلسة
    session = SessionState.query.filter_by(user_phone=phone).first()
    if not session:
        session = SessionState(user_phone=phone, step='start', data='{}')
        db.session.add(session)
        db.session.commit()

    # خطوات السيناريو
    step = session.step
    data = json.loads(session.data or '{}')
    reply = ''

    if step == 'start':
        if incoming_msg.lower() in ['ابدأ', 'start']:
            session.step = 'choose_service'
            reply = 'مرحباً بك في متجر رييل لتبديل العملات!\nاختر الخدمة المطلوبة:\n1. تبديل عملة'
        else:
            reply = 'أرسل "ابدأ" أو "start" للمتابعة.'
    elif step == 'choose_service':
        if incoming_msg.strip() == '1':
            session.step = 'choose_currency_from'
            reply = 'اختر العملة التي تريد استبدالها:\n1. جنيه سوداني\n2. شلن أوغندي'
        else:
            reply = 'يرجى اختيار رقم الخدمة من القائمة.'
    elif step == 'choose_currency_from':
        if incoming_msg == '1':
            data['from_currency'] = 'SDG'
            session.step = 'choose_currency_to'
            reply = 'اختر العملة التي تريد استلامها:\n1. شلن أوغندي\n2. جنيه سوداني'
        elif incoming_msg == '2':
            data['from_currency'] = 'UGX'
            session.step = 'choose_currency_to'
            reply = 'اختر العملة التي تريد استلامها:\n1. جنيه سوداني\n2. شلن أوغندي'
        else:
            reply = 'يرجى اختيار رقم العملة من القائمة.'
    elif step == 'choose_currency_to':
        if incoming_msg == '1':
            data['to_currency'] = 'UGX' if data.get('from_currency') == 'SDG' else 'SDG'
            # جلب سعر الصرف
            rate = ExchangeRate.query.filter_by(from_currency=data['from_currency'], to_currency=data['to_currency']).first()
            if rate:
                data['rate'] = rate.rate
                session.step = 'confirm_exchange'
                reply = f"سعر الصرف الحالي: 1 {data['from_currency']} = {rate.rate} {data['to_currency']}\nهل ترغب في الاستبدال؟ (نعم/لا)"
            else:
                reply = 'عذراً، لا يوجد سعر صرف متاح حالياً لهذا الزوج.'
                session.step = 'start'
        elif incoming_msg == '2':
            data['to_currency'] = data.get('from_currency')
            reply = 'لا يمكن استبدال العملة بنفسها. اختر عملة مختلفة.'
        else:
            reply = 'يرجى اختيار رقم العملة من القائمة.'
    elif step == 'confirm_exchange':
        if incoming_msg.strip() in ['نعم', 'yes']:
            session.step = 'enter_amount'
            reply = f"يرجى إدخال المبلغ الذي تريد استبداله بـ {data['from_currency']}"
        elif incoming_msg.strip() in ['لا', 'no']:
            session.step = 'start'
            reply = 'تم إلغاء العملية. أرسل "ابدأ" للبدء من جديد.'
        else:
            reply = 'يرجى الرد بـ "نعم" أو "لا".'
    elif step == 'enter_amount':
        try:
            amount = float(incoming_msg)
            data['amount'] = amount
            received = round(amount * data['rate'], 2)
            data['received_amount'] = received
            session.step = 'choose_withdraw_method'
            reply = f"ستستلم: {received} {data['to_currency']}\nاختر طريقة السحب:\n1. من المكتب\n2. أونلاين (وكيل)"
        except Exception:
            reply = 'يرجى إدخال مبلغ صحيح.'
    elif step == 'choose_withdraw_method':
        if incoming_msg == '1':
            data['withdraw_method'] = 'office'
            session.step = 'show_account_info'
            reply = 'يرجى إرسال رقم الحساب الذي سترسل إليه المبلغ مع كتابة التعليق في الإشعار.'
        elif incoming_msg == '2':
            data['withdraw_method'] = 'online'
            session.step = 'show_account_info'
            reply = 'يرجى إرسال رقم الحساب الذي سترسل إليه المبلغ مع كتابة التعليق في الإشعار.'
        else:
            reply = 'يرجى اختيار طريقة السحب من القائمة.'
    elif step == 'show_account_info':
        # في هذه الخطوة، البوت ينتظر من المستخدم تأكيد إرسال المبلغ
        session.step = 'wait_payment_confirmation'
        reply = 'بعد إرسال المبلغ، أرسل كلمة "تم".'
    elif step == 'wait_payment_confirmation':
        if incoming_msg.strip() in ['تم', 'done']:
            # حفظ العملية في قاعدة البيانات
            user = User.query.filter_by(phone=phone).first()
            if not user:
                user = User(phone=phone)
                db.session.add(user)
                db.session.commit()
            transaction = Transaction(
                user_id=user.id,
                from_currency=data['from_currency'],
                to_currency=data['to_currency'],
                amount=data['amount'],
                received_amount=data['received_amount'],
                status='pending',
                method=data['withdraw_method'],
                notes=''
            )
            db.session.add(transaction)
            db.session.commit()
            session.step = 'start'
            reply = 'تم استلام طلبك وجاري معالجته من قبل الإدارة. سيتم إشعارك عند اكتمال العملية.'
            # هنا يمكن إضافة إشعار للمدير لاحقاً
        else:
            reply = 'يرجى إرسال كلمة "تم" بعد إرسال المبلغ.'
    else:
        # إذا لم يتم التعرف على الرسالة في السيناريو، ابحث في الأسئلة الشائعة
        faq = FAQ.query.filter(FAQ.question.ilike(f"%{incoming_msg}%")).first()
        if faq:
            reply = faq.answer
        else:
            # إذا لم توجد إجابة، استخدم الذكاء الاصطناعي
            try:
                from ai_utils import ask_openai
                ai_reply = ask_openai(incoming_msg)
                reply = ai_reply
            except Exception:
                reply = 'عذراً، لا يمكن معالجة استفسارك حالياً.'
        session.step = 'start'

    # حفظ حالة الجلسة
    session.data = json.dumps(data, ensure_ascii=False)
    db.session.commit()
    return build_twilio_response(reply)

if __name__ == '__main__':
    if not os.path.exists('exchange.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
