import os
import requests

def ask_openai(question):
    """
    إرسال السؤال إلى نموذج ذكاء اصطناعي مجاني (HuggingFace أو أي خدمة مجانية)
    """
    try:
        from app import db, AppConfig
        api_url_row = AppConfig.query.filter_by(key='AI_API_URL').first()
        api_url = api_url_row.value if api_url_row else ''
    except Exception:
        api_url = ''
    if not api_url:
        return 'عذراً، خدمة الذكاء الاصطناعي غير مفعلة حالياً.'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'inputs': question,
        'parameters': {"max_new_tokens": 120, "return_full_text": False},
        'options': {"wait_for_model": True}
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            # دعم صيغ مختلفة من الرد حسب النموذج
            if isinstance(result, list) and 'generated_text' in result[0]:
                return result[0]['generated_text'].strip()
            elif 'generated_text' in result:
                return result['generated_text'].strip()
            elif 'answer' in result:
                return result['answer'].strip()
            else:
                return str(result)
        else:
            return 'عذراً، حدث خطأ في خدمة الذكاء الاصطناعي.'
    except Exception:
        return 'عذراً، خدمة الذكاء الاصطناعي غير متاحة حالياً.'
