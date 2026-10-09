import json
import sys
from pathlib import Path

import notifier
import scraper

STATE = Path(__file__).with_name("seen_courses.json")

# Takip kapsamı değişince artırılır: mevcut kurslar bildirimsiz yeniden kaydedilir.
STATE_VERSION = 2


def load_state():
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
        if state.get("version") == STATE_VERSION:
            return state
        return {"version": STATE_VERSION, "initialized": False, "seen": state.get("seen", {})}
    return {"version": STATE_VERSION, "initialized": False, "seen": {}}


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def send_examples():
    """Bağlantı testi + gerçek verilerle örnek bildirimler (state'e dokunmaz)."""
    label = "🧪 <i>ÖRNEK / TEST — bu gerçek bir yeni kurs bildirimi değildir</i>\n\n"
    notifier.send("✅ <b>MEB Kurs Takip</b>: Telegram bağlantısı çalışıyor. Örnek bildirimler geliyor 👇")
    courses = scraper.fetch_courses()
    special = [c for c in courses if scraper.is_special(c)]
    other = [c for c in courses if not scraper.is_special(c)]
    if special:
        notifier.send(label + notifier.format_special(special[0]))
    notifier.send(label + notifier.format_digest(other[:3])[0])
    print("Telegram test ve örnek mesajları gönderildi.")


def main():
    if "--test-telegram" in sys.argv:
        send_examples()
        return

    state = load_state()
    courses = scraper.fetch_courses()
    print(f"Takip edilen ilçelerdeki kurs sayısı: {len(courses)}")

    # Kurs No MEB tarafından verilen benzersiz ID'dir; state anahtarı olarak bunu kullanıyoruz.
    new = [c for c in courses if c["id"] not in state["seen"]]
    special = [c for c in new if scraper.is_special(c)]
    other = [c for c in new if not scraper.is_special(c)]

    if not state["initialized"]:
        print(f"İlk çalıştırma: {len(new)} mevcut kurs kaydedildi, bildirim gönderilmedi.")
    else:
        for c in special:
            print(f"Yeni özel kurs: {c['id']} {c['ilce']} {c['baslangic']}")
            notifier.send(notifier.format_special(c))
        if other:
            print(f"Yeni diğer kurslar: {', '.join(c['id'] for c in other)}")
            for msg in notifier.format_digest(other):
                notifier.send(msg)

    for c in new:
        state["seen"][c["id"]] = {k: c[k] for k in ("kurs_adi", "ilce", "baslangic", "bitis")}
    state["initialized"] = True
    save_state(state)
    print(f"Yeni: {len(new)} (özel: {len(special)}), toplam görülen: {len(state['seen'])}")


if __name__ == "__main__":
    main()
