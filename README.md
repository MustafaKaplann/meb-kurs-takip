# meb-kurs-takip

Checks the [MEB e-Yaygın course list](https://e-yaygin.meb.gov.tr/pageKurslar.aspx) every 15 minutes with GitHub Actions and sends a Telegram message for **new** courses.

## What it reports

| Notification | Condition |
|---|---|
| 🚨 **Separate alert** | Mersin · Mezitli or Yenişehir · `Havuz Suyu Operatörlüğü` · `Yüzyüze Eğitim` |
| 🆕 **Summary list** | Any other new course opened in Mersin's Mezitli or Yenişehir districts (one message per run; a long list is split into several messages) |

Nationwide online courses that have no province or district are not included.

## How it works

1. `scraper.py` loads the page, fills in the ASP.NET form (il: Mersin, ilçe: Mezitli / Yenişehir) and posts it. It reads every page of the results, 100 rows per page.
2. `main.py` compares the results with `seen_courses.json`, using the MEB "Kurs No" as each course's unique ID.
   - **First run** (or after the tracking scope changes, i.e. `STATE_VERSION` is increased): stores the existing courses and sends **no** notification.
   - **Later runs:** sends notifications only for courses not seen before, then adds them to the file.
3. The workflow (`.github/workflows/check-courses.yml`) commits the updated `seen_courses.json` back to the repository with the message `chore: update seen courses`.

## Setup

In the repository, open Settings → Secrets and variables → Actions and add these secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The token appears nowhere in the code.

## Usage

- **Automatic:** runs every 15 minutes (`*/15 * * * *`). GitHub may start it a few minutes late.
- **Manual:** Actions → *Check MEB Courses* → *Run workflow*.
  - Tick `test_telegram` to send only a test message.
- **Local test:** `pip install -r requirements.txt && python scraper.py` shows course counts per district and the matching 🚨 courses.

To change the districts or the special course, edit the constants at the top of `scraper.py` (`ILCELER`, `OZEL_KURS_ADI`). Also increase `STATE_VERSION` in `main.py`, so that existing courses are recorded without sending notifications.

Note: GitHub turns off scheduled workflows after 60 days with no activity in the repository. If that happens, re-enable the workflow from the Actions tab.
