"""MEB e-Yaygın kurs listesini çeker.

Sayfa ASP.NET WebForms + Telerik kontrolleri kullanıyor; ayrı bir JSON API yok.
Bu yüzden sayfayı GET ile alıp form alanlarını (ViewState vb.) doldurarak
il/ilçe seçilmiş ve "Kursları Listele" butonuna basılmış gibi POST gönderiyoruz.
Sonuç tablosu sayfa başına 100 kayıt gösterir; diğer sayfalar pager linklerinin
postback'leriyle alınır.
"""
import json
import re

import requests
from bs4 import BeautifulSoup

URL = "https://e-yaygin.meb.gov.tr/pageKurslar.aspx"

IL = "Mersin"
ILCELER = ["Mezitli", "Yenişehir"]

# Özel (🚨) bildirim gönderilecek kurs
OZEL_KURS_ADI = "Havuz Suyu Operatörlüğü"
OZEL_EGITIM_SEKLI = "Yüzyüze Eğitim"

# Grid başlığı -> sonuç sözlüğündeki alan adı
COLUMNS = {
    "Kurs No": "id",
    "Kurs Adı": "kurs_adi",
    "İl": "il",
    "İlçe": "ilce",
    "Kurum": "kurum",
    "Eğitim Şekli": "egitim_sekli",
    "Kursun Yapılacağı Yer": "yer",
    "Baş.Tarihi": "baslangic",
    "Bit.Tarihi": "bitis",
    "Süre": "sure",
    "Kontenjan": "kontenjan",
}

MAX_PAGES = 50  # sonsuz döngüye karşı güvenlik


def _norm(text):
    return " ".join(text.replace("İ", "i").replace("I", "ı").lower().split())


def _form_fields(soup):
    return {
        i["name"]: i.get("value", "")
        for i in soup.select("input[name]")
        if i.get("type") not in ("submit", "button", "checkbox", "image")
    }


def _combo_codes(soup, combo_id):
    names = [li.get_text(strip=True) for li in soup.select(f"#{combo_id}_DropDown li")]
    m = re.search(rf'"_uniqueId":"{combo_id}".*?"itemData":(\[.*?\])', soup.decode(), re.S)
    if not m:
        raise RuntimeError(f"{combo_id} listesi sayfada bulunamadı (site yapısı değişmiş olabilir).")
    return dict(zip(names, (d["value"] for d in json.loads(m.group(1)))))


def _combo_state(value, text):
    return json.dumps({
        "logEntries": [], "value": value, "text": text, "enabled": True,
        "checkedIndices": [], "checkedItemsTextOverflows": False,
    })


def _parse_rows(soup):
    headers = [th.get_text(" ", strip=True) for th in soup.select("#rgKurslar_ctl00_Header th")]
    if "Kurs No" not in headers:
        raise RuntimeError("Kurs tablosu bulunamadı (site yapısı değişmiş olabilir).")
    courses = []
    for tr in soup.select("#rgKurslar_ctl00 > tbody > tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) != len(headers):
            continue  # "kayıt yok" satırı
        row = {COLUMNS[h]: v for h, v in zip(headers, cells) if h in COLUMNS}
        if row.get("id"):
            courses.append(row)
    return courses


def _next_page_target(soup):
    """Bir sonraki sayfanın postback hedefini döndürür, son sayfadaysa None."""
    current = soup.select_one(".rgPager a.rgCurrentPage")
    if not current:
        return None
    nxt = current.find_next_sibling("a")
    if not nxt or not nxt.get_text(strip=True).isdigit():
        return None
    m = re.search(r"__doPostBack\('([^']+)'", nxt.get("href", ""))
    return m.group(1) if m else None


def fetch_district(session, ilce):
    """Verilen ilçedeki tüm kursları (tüm sayfalar) döndürür."""
    soup = BeautifulSoup(session.get(URL, timeout=60).text, "html.parser")
    il_kodu = _combo_codes(soup, "cmbKursIlKodu")[IL]
    selection = {
        "cmbKursIlKodu": IL,
        "cmbKursIlKodu_ClientState": _combo_state(il_kodu, IL),
    }

    def post(soup, extra):
        form = _form_fields(soup)
        form.update({"__EVENTTARGET": "", "__EVENTARGUMENT": ""})
        form.update(selection)
        form.update(extra)
        resp = session.post(URL, data=form, timeout=90)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    # İl seçimi -> ilçe listesi yüklenir
    soup = post(soup, {
        "__EVENTTARGET": "cmbKursIlKodu",
        "__EVENTARGUMENT": json.dumps({"Command": "Select", "Index": 0}),
    })
    ilce_kodu = _combo_codes(soup, "cmbKursIlceKodu").get(ilce)
    if not ilce_kodu:
        raise RuntimeError(f"'{ilce}' ilçe listesinde yok.")
    selection.update({
        "cmbKursIlceKodu": ilce,
        "cmbKursIlceKodu_ClientState": _combo_state(ilce_kodu, ilce),
    })

    soup = post(soup, {"btnSearch": "Kursları Listele"})
    courses = _parse_rows(soup)
    for _ in range(MAX_PAGES):
        target = _next_page_target(soup)
        if not target:
            break
        soup = post(soup, {"__EVENTTARGET": target})
        courses += _parse_rows(soup)

    # Beklenen kayıt sayısıyla karşılaştır ("295 kayıttan 1 - 100.")
    info = soup.select_one(".rgInfoPart")
    m = re.search(r"(\d+)\s*kayıttan", info.get_text() if info else "")
    if m and int(m.group(1)) != len(courses):
        raise RuntimeError(f"{ilce}: {m.group(1)} kayıt bekleniyordu, {len(courses)} okundu.")
    return courses


def fetch_courses():
    """Takip edilen ilçelerdeki tüm kursları döndürür."""
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (meb-kurs-takip)"
    courses = {}
    for ilce in ILCELER:
        for c in fetch_district(s, ilce):
            if _norm(c["ilce"]) == _norm(ilce):
                courses[c["id"]] = c
    return list(courses.values())


def is_special(c):
    return (
        _norm(c["kurs_adi"]) == _norm(OZEL_KURS_ADI)
        and _norm(c["egitim_sekli"]) == _norm(OZEL_EGITIM_SEKLI)
    )


if __name__ == "__main__":
    all_courses = fetch_courses()
    for ilce in ILCELER:
        print(f"{IL} / {ilce}: {sum(c['ilce'] == ilce for c in all_courses)} kurs")
    for c in all_courses:
        if is_special(c):
            print("🚨 " + json.dumps(c, ensure_ascii=False))
