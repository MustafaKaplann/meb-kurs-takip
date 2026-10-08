# meb-kurs-takip

Checks the [MEB e-Yaygın course list](https://e-yaygin.meb.gov.tr/pageKurslar.aspx) every hour with GitHub Actions and sends a Telegram notification when a matching **new** course appears.

**Filters:** İl `Mersin` · İlçe `Mezitli` or `Yenişehir` · Kurs `Havuz Suyu Operatörlüğü` · Eğitim Şekli `Yüzyüze Eğitim`

## How it works

1. `scraper.py` loads the page, fills in the ASP.NET form (Mersin + course name) and posts it, as if you clicked "Kursları Listele". It then parses the result table and keeps only the courses that match the filters above.
2. `main.py` compares the results with `seen_courses.json`, using the MEB "Kurs No" as each course's unique ID.
   - **First run:** stores the existing courses and sends **no** notification.
   - **Later runs:** sends a Telegram message only for courses not seen before, then adds them to the file.
3. The workflow (`.github/workflows/check-courses.yml`) commits the updated `seen_courses.json` back to the repository with the message `chore: update seen courses`.

## Setup

In the repository, open Settings → Secrets and variables → Actions and add these secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The token appears nowhere in the code.

## Usage

- **Automatic:** runs every hour (`0 * * * *`). GitHub may start it a few minutes late.
- **Manual:** Actions → *Check MEB Courses* → *Run workflow*.
  - Tick `test_telegram` to send only a test message.
- **Local test:** `pip install -r requirements.txt && python scraper.py` lists the courses found, marking the matching ones with ✔.

To change the filters, edit the constants at the top of `scraper.py`.

Note: GitHub turns off scheduled workflows after 60 days with no activity in the repository. If that happens, re-enable the workflow from the Actions tab.
