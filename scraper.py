"""MEB e-Yaygın kurs listesini çeker.

Sayfa ASP.NET WebForms + Telerik kontrolleri kullanıyor; ayrı bir JSON API yok.
Bu yüzden sayfayı GET ile alıp form alanlarını (ViewState vb.) doldurarak
"Kursları Listele" butonuna basılmış gibi POST gönderiyoruz.
"""
import json
import re

import requests
from bs4 import BeautifulSoup

URL = "https://e-yaygin.meb.gov.tr/pageKurslar.aspx"

IL = "Mersin"
ILCELER = {"mezitli", "yenişehir"}
KURS_ADI = "Havuz Suyu Operatörlüğü"
EGITIM_SEKLI = "yüzyüze eğitim"

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


def _norm(text):
    return " ".join(text.replace("İ", "i").replace("I", "ı").lower().split())


def _form_fields(soup):
    return {
        i["name"]: i.get("value", "")
        for i in soup.select("input[name]")
        if i.get("type") not in ("submit", "button", "checkbox", "image")
    }


def _il_kodu(soup, il):
    names = [li.get_text(strip=True) for li in soup.select("#cmbKursIlKodu_DropDown li")]
    m = re.search(r'"_uniqueId":"cmbKursIlKodu".*?"itemData":(\[.*?\])', soup.decode(), re.S)
    if not m:
        raise RuntimeError("İl listesi sayfada bulunamadı (site yapısı değişmiş olabilir).")
    codes = dict(zip(names, (d["value"] for d in json.loads(m.group(1)))))
    if il not in codes:
        raise RuntimeError(f"'{il}' il listesinde yok.")
    return codes[il]


def fetch_all(il=IL, kurs_adi=KURS_ADI):
    """Verilen il ve kurs adı için sitedeki tüm kursları döndürür (filtrelenmemiş)."""
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (meb-kurs-takip)"
    resp = s.get(URL, timeout=60)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    form = _form_fields(soup)
    form.update({
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "cmbKursIlKodu": il,
        "cmbKursIlKodu_ClientState": json.dumps({
            "logEntries": [], "value": _il_kodu(soup, il), "text": il, "enabled": True,
            "checkedIndices": [], "checkedItemsTextOverflows": False,
        }),
        "txtKursAdi": kurs_adi,
        "txtKursAdi_ClientState": json.dumps({
            "enabled": True, "emptyMessage": "", "validationText": kurs_adi,
            "valueAsString": kurs_adi, "lastSetTextBoxValue": kurs_adi,
        }),
        "btnSearch": "Kursları Listele",
    })
    resp = s.post(URL, data=form, timeout=90)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

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


def matches(c):
    return (
        _norm(c["il"]) == _norm(IL)
        and _norm(c["ilce"]) in ILCELER
        and _norm(c["kurs_adi"]) == _norm(KURS_ADI)
        and _norm(c["egitim_sekli"]) == EGITIM_SEKLI
    )


def fetch_matching():
    return [c for c in fetch_all() if matches(c)]


if __name__ == "__main__":
    all_courses = fetch_all()
    print(f"{IL} / '{KURS_ADI}' araması: {len(all_courses)} kurs")
    for c in all_courses:
        print(("✔ " if matches(c) else "  ") + json.dumps(c, ensure_ascii=False))
