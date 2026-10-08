import json
import sys
from pathlib import Path

import notifier
import scraper

STATE = Path(__file__).with_name("seen_courses.json")


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"initialized": False, "seen": {}}


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if "--test-telegram" in sys.argv:
        notifier.send("✅ <b>MEB Kurs Takip</b>: Telegram bağlantısı çalışıyor.")
        print("Telegram test mesajı gönderildi.")
        return

    state = load_state()
    courses = scraper.fetch_matching()
    print(f"Uygun kurs sayısı: {len(courses)}")

    # Kurs No MEB tarafından verilen benzersiz ID'dir; state anahtarı olarak bunu kullanıyoruz.
    new = [c for c in courses if c["id"] not in state["seen"]]

    if not state["initialized"]:
        print(f"İlk çalıştırma: {len(new)} mevcut kurs kaydedildi, bildirim gönderilmedi.")
    else:
        for c in new:
            print(f"Yeni kurs: {c['id']} {c['ilce']} {c['baslangic']}")
            notifier.send(notifier.format_course(c))

    for c in new:
        state["seen"][c["id"]] = {k: c[k] for k in ("kurs_adi", "ilce", "baslangic", "bitis")}
    state["initialized"] = True
    save_state(state)
    print(f"Yeni: {len(new)}, toplam görülen: {len(state['seen'])}")


if __name__ == "__main__":
    main()
