from flask import Blueprint, render_template, request, redirect, url_for, flash

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings/twilio', methods=['GET', 'POST'])
def twilio_settings():
    from models import db, AppConfig
    keys = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER']
    values = {k: '' for k in keys}
    for k in keys:
        row = AppConfig.query.filter_by(key=k).first()
        if row:
            values[k] = row.value
    if request.method == 'POST':
        for k in keys:
            v = request.form.get(k, '')
            row = AppConfig.query.filter_by(key=k).first()
            if row:
                row.value = v
            else:
                db.session.add(AppConfig(key=k, value=v))
        db.session.commit()
        flash('تم حفظ إعدادات Twilio بنجاح', 'success')
        return redirect(url_for('settings.twilio_settings'))
    return render_template('settings_twilio.html', values=values)

@settings_bp.route('/settings/ai', methods=['GET', 'POST'])
def ai_settings():
    from models import db, AppConfig
    keys = ['AI_API_URL']
    values = {k: '' for k in keys}
    for k in keys:
        row = AppConfig.query.filter_by(key=k).first()
        if row:
            values[k] = row.value
    if request.method == 'POST':
        for k in keys:
            v = request.form.get(k, '')
            row = AppConfig.query.filter_by(key=k).first()
            if row:
                row.value = v
            else:
                db.session.add(AppConfig(key=k, value=v))
        db.session.commit()
        flash('تم حفظ إعدادات الذكاء الاصطناعي بنجاح', 'success')
        return redirect(url_for('settings.ai_settings'))
    return render_template('settings_ai.html', values=values)
