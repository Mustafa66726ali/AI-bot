import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

def get_twilio_config():
    try:
        from app import db, AppConfig
        sid = AppConfig.query.filter_by(key='TWILIO_ACCOUNT_SID').first()
        token = AppConfig.query.filter_by(key='TWILIO_AUTH_TOKEN').first()
        number = AppConfig.query.filter_by(key='TWILIO_WHATSAPP_NUMBER').first()
        return (sid.value if sid else '', token.value if token else '', number.value if number else '')
    except Exception:
        return ('', '', '')

def send_whatsapp_message(to, message):
    from twilio.rest import Client
    sid, token, number = get_twilio_config()
    if not sid or not token or not number:
        return None
    client = Client(sid, token)
    return client.messages.create(
        body=message,
        from_=number,
        to=to
    )

def build_twilio_response(message):
    resp = MessagingResponse()
    resp.message(message)
    return str(resp)
