import html
import os

import requests

LIST_URL = "https://e-yaygin.meb.gov.tr/pageKurslar.aspx"


def format_course(c):
    e = lambda k: html.escape(c.get(k, "") or "-")
    return (
        "🚨 <b>Yeni MEB Kursu Bulundu!</b>\n\n"
        f"📚 <b>Kurs:</b> {e('kurs_adi')}\n"
        f"🆔 <b>Kurs No:</b> {e('id')}\n"
        f"📍 <b>İl / İlçe:</b> {e('il')} / {e('ilce')}\n"
        f"🏫 <b>Kurum:</b> {e('kurum')}\n"
        f"🏠 <b>Yer:</b> {e('yer')}\n"
        f"🎓 <b>Eğitim:</b> {e('egitim_sekli')}\n"
        f"📅 <b>Başlangıç:</b> {e('baslangic')}\n"
        f"📅 <b>Bitiş:</b> {e('bitis')}\n"
        f"⏱ <b>Süre:</b> {e('sure')} saat\n"
        f"👥 <b>Kontenjan:</b> {e('kontenjan')}\n\n"
        f"🔗 <a href=\"{LIST_URL}\">Kurs listesi</a> (İl: Mersin, Kurs No: {e('id')} ile arayın)"
    )


def send(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
              "disable_web_page_preview": "true"},
        timeout=30,
    )
    if not r.ok:
        # URL'yi (token içerir) değil, sadece Telegram'ın açıklamasını göster
        desc = r.json().get("description", "") if r.headers.get("content-type", "").startswith("application/json") else ""
        raise RuntimeError(f"Telegram hatası {r.status_code}: {desc}")
