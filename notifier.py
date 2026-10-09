import html
import os
import time

import requests

LIST_URL = "https://e-yaygin.meb.gov.tr/pageKurslar.aspx"
MAX_LEN = 3800  # Telegram sınırı 4096 karakter


def _e(c, k):
    return html.escape(c.get(k, "") or "-")


def format_special(c):
    return (
        "🚨 <b>Yeni MEB Kursu Bulundu!</b>\n\n"
        f"📚 <b>Kurs:</b> {_e(c, 'kurs_adi')}\n"
        f"🆔 <b>Kurs No:</b> {_e(c, 'id')}\n"
        f"📍 <b>İl / İlçe:</b> {_e(c, 'il')} / {_e(c, 'ilce')}\n"
        f"🏫 <b>Kurum:</b> {_e(c, 'kurum')}\n"
        f"🏠 <b>Yer:</b> {_e(c, 'yer')}\n"
        f"🎓 <b>Eğitim:</b> {_e(c, 'egitim_sekli')}\n"
        f"📅 <b>Başlangıç:</b> {_e(c, 'baslangic')}\n"
        f"📅 <b>Bitiş:</b> {_e(c, 'bitis')}\n"
        f"⏱ <b>Süre:</b> {_e(c, 'sure')} saat\n"
        f"👥 <b>Kontenjan:</b> {_e(c, 'kontenjan')}\n\n"
        f"🔗 <a href=\"{LIST_URL}\">Kurs listesi</a> (İl: Mersin, Kurs No: {_e(c, 'id')} ile arayın)"
    )


def format_digest(courses):
    """Yeni kursları tek (gerekirse birkaç) mesajda listeler."""
    header = f"🆕 <b>Mezitli / Yenişehir'de {len(courses)} yeni kurs</b>\n"
    blocks = [
        f"\n📚 <b>{_e(c, 'kurs_adi')}</b>\n"
        f"📍 {_e(c, 'ilce')} · {_e(c, 'kurum')}\n"
        f"🎓 {_e(c, 'egitim_sekli')} · ⏱ {_e(c, 'sure')} saat · 👥 {_e(c, 'kontenjan')}\n"
        f"📅 {_e(c, 'baslangic')} → {_e(c, 'bitis')} · 🆔 {_e(c, 'id')}\n"
        for c in sorted(courses, key=lambda c: (c["ilce"], c["kurs_adi"]))
    ]
    footer = f"\n🔗 <a href=\"{LIST_URL}\">Kurs listesi</a>"
    messages, current = [], header
    for b in blocks:
        if len(current) + len(b) > MAX_LEN:
            messages.append(current)
            current = "🆕 <b>(devam)</b>\n"
        current += b
    messages.append(current + footer)
    return messages


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
    time.sleep(1)  # Telegram hız sınırı
