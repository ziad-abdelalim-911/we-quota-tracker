# we-quota-tracker

A Python automation tool that tracks your **WE (Telecom Egypt) home internet quota** daily and logs usage data to a PostgreSQL database. Sends a daily Telegram notification with your quota summary. Can be run locally or fully automated via GitHub Actions.

---

## Table of Contents

- [How it works](#how-it-works)
- [Project Structure](#project-structure)
- [Automated Daily Runs](#automated-daily-runs)
- [How to Run Locally](#how-to-run-locally)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## How it works

1. Authenticates with the WE API using your landline credentials.
2. Fetches your current quota details.
3. Calculates your daily usage and whether you are over or under your expected overall usage.
4. Logs a row to a PostgreSQL `quota_log` table.
5. Sends a Telegram notification with your daily quota summary.
6. Runs automatically every day via GitHub Actions scheduled workflow.

> **Note:** On the 1st day of every cycle, the table is automatically cleared for a fresh monthly log.

| Column           | Type          | Description                                                    |
| ---------------- | ------------- | -------------------------------------------------------------- |
| `id`             | SERIAL        | Auto-incremented primary key                                   |
| `date_time`      | TIMESTAMP     | Timestamp of the record                                        |
| `day`            | INT           | Current day in the quota cycle (1–30)                          |
| `usage_gbs`      | NUMERIC(10,1) | GBs used in this day                                           |
| `remaining_gbs`  | NUMERIC(10,1) | Remaining quota at time of record                              |
| `overall_state`  | VARCHAR(50)   | `Under` or `Over` expected overall usage                       |
| `state_gbs`      | NUMERIC(10,1) | How many GBs under or over                                     |
| `state_days`     | NUMERIC(10,1) | How many days ahead or behind your expected usage pace         |
| `remaining_days` | INT           | Days left until quota renewal                                   |

---

## Project Structure

```
we-quota-tracker/
├── src/
│   ├── main.py          # Entry point — orchestrates the full flow
│   ├── api_client.py    # WE API authentication and quota fetching
│   ├── quota.py         # Quota calculations (usage, state, days)
│   ├── db.py            # PostgreSQL connection and record insertion
│   ├── notifier.py      # Telegram notification sender
│   ├── config.py        # Environment variable loading
│   └── utils.py         # Utility helpers (e.g. internet connectivity check)
├── .github/
│   └── workflows/
│       └── daily_tracker.yml   # GitHub Actions scheduled workflow
├── requirements.txt
└── .env                 # Local environment variables (not committed)
```

---

## Automated Daily Runs

### 1. Fork or push the repo to GitHub

### 2. Set up a PostgreSQL database

You can use any PostgreSQL database you already have. If you don't have one, you'll need a cloud-hosted database so the script can connect to it from GitHub Actions.

**My recommendation: [Neon](https://neon.tech)**

Neon is a free cloud-hosted PostgreSQL database. Since both GitHub Actions and Neon are on the cloud, the script runs fully automatically with nothing running on your machine — no local database, no local server, nothing to worry about.

Here's how to get started with Neon:

1. Go to [neon.tech](https://neon.tech) and create a free account.
2. Click **New Project** and give it a name.
3. Once created, go to **Connection Details**.
4. Copy the connection string — it looks like:

   ```
   postgresql://user:password@host/dbname?sslmode=require
   ```

5. Use this as your `DATABASE_URL` in the next step.

### 3. Set up a Telegram bot (optional but recommended)

>**Video guide:** [How to create a Telegram bot and get your chat ID](https://youtu.be/N8HsT58tXJg?si=pC4WeZIsPIZJMIYF)

The script sends a daily Telegram message with your quota summary. To enable this:

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts to create a bot.
3. Copy the **bot token** you receive.
4. Start a conversation with your new bot, then visit:

   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
5. Send a message to your bot and refresh the URL — you'll see your **chat ID** in the response.

> **Note:** If you skip this step, just omit the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets. The script will still run and log to the database; quota details will be printed to the Actions log instead.

### 4. Add your secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add each of the following:

| Secret Name           | Description                              |
| --------------------- | ---------------------------------------- |
| `LND_NUMBER`          | Your WE landline number                  |
| `LND_PASS`            | Your WE password                         |
| `START_GB`            | Your total monthly quota in GB           |
| `DATABASE_URL`        | Your PostgreSQL connection string        |
| `TELEGRAM_BOT_TOKEN`  | Your Telegram bot token *(optional)*     |
| `TELEGRAM_CHAT_ID`    | Your Telegram chat ID *(optional)*       |

> **Note:** Secret names are case-sensitive. They must match exactly as shown above.

### 5. You're all set!

That's everything — the workflow is ready to go. It will run automatically every day at **9 PM Cairo time (UTC+2)** without any further setup.

To test it or trigger it manually at any time, go to the **Actions** tab → **Daily Quota Tracker** → **Run workflow**.

If the workflow ran successfully, a new record will be added to your `quota_log` table and you'll receive a Telegram message like this:

```
Quota Report — Day 9
━━━━━━━━━━━━━━━━━━━━
Usage Today: 4.3 GB
Remaining: 268.8 / 400.0 GB (32.8% used)
Days Left: 21
Overall State: Over by 11.2 GB (0.8 days)
━━━━━━━━━━━━━━━━━━━━
```

If Telegram is not configured, the same info will appear in the Actions log instead:

```
INFO:root:─── Quota Record Saved ───────────────────
INFO:root:  Day            : 9
INFO:root:  Usage Today    : 4.3 GB
INFO:root:  Remaining      : 268.8 / 400.0 GB (32.8% used)
INFO:root:  Remaining Days : 21
INFO:root:  Overall State  : Over by 11.2 GB (0.8 days)
INFO:root:──────────────────────────────────────────
```

---

## How to Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/Kareem74x/we-quota-tracker.git
cd we-quota-tracker
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Create a `.env` file** in the project root with the following variables:

```env
# WE account credentials
LND_NUMBER=0123456789       # Your WE landline number
LND_PASS=yourpassword       # Your WE password

# Quota settings
START_GB=100                # Your quota size in GB

# PostgreSQL connection string
# Works with any PostgreSQL provider: Neon, Supabase, Railway, or self-hosted
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Telegram notifications (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

**4. Run the script**

```bash
python src/main.py
```

If successful, a record will be inserted into your database and you'll receive a Telegram notification (or see the summary in your terminal if Telegram is not configured).

---

## Acknowledgements

The API request and authentication logic in this project was adapted from [TE-QuotaCheck](https://github.com/karimawi/TE-QuotaCheck) by [karimawi](https://github.com/karimawi).

---

## License

This project is licensed under the [MIT License](LICENSE).