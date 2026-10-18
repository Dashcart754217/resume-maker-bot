# 📄 Professional Resume Maker Telegram Bot

A full-featured Telegram Bot built in Python that creates **clean, ATS-compliant, job-ready PDF resumes** for users with custom headshot photos, experience, education, skills, and certifications.

Designed to be hosted **24/7 on Railway via GitHub** with zero server maintenance.

---

## 🌟 Key Features

1. **📸 Headshot Profile Photo Support**:
   - Automatically crops user photos into modern, high-resolution circular frames.
   - Works seamlessly with or without photo (header auto-adjusts layout).

2. **⏭️ Skip Feature on Every Step**:
   - Every single prompt has an inline `[⏭️ Skip this step]` button and `/skip` command support.
   - Freshers or experienced pros can skip whatever doesn't apply to them (Photo, Experience, Certifications, etc.).

3. **✏️ Dedicated Review & Edit Dashboard**:
   - Before downloading (and anytime after), users get an interactive dashboard.
   - Edit any specific section (`✏️ Name`, `✏️ Contact`, `✏️ Summary`, `✏️ Skills`, `✏️ Experience`, `✏️ Education`, `✏️ Certifications`, `📸 Photo`) without starting over.

4. **🎨 4 Professional Color Themes**:
   - 👔 **Modern Navy**: Deep navy blue headers with slate accents.
   - 🌲 **Executive Emerald**: Forest emerald green with subtle green lines.
   - 🖤 **Classic Charcoal**: High-contrast dark graphite (ATS favorite).
   - 🍷 **Royal Burgundy**: Elegant deep wine styling.

5. **📄 Instant PDF Generation**:
   - Uses `ReportLab` to compile clean vector-quality PDFs.
   - Formatted for Standard Letter / A4 paper with ATS-compliant margins and structure.
   - Sends the PDF directly in the chat (`Resume_<Name>.pdf`).

---

## 🚀 Step 1: Get Telegram Bot Token

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`.
3. Enter a display name (e.g. `My Job Resume Maker`).
4. Enter a username ending in `bot` (e.g. `my_job_resumemaker_bot`).
5. Copy your **HTTP API Token** (e.g., `8123456789:AAFx...`).

---

## 💻 Step 2: Test Locally (Windows)

1. Open `config.py` and paste your Bot Token:
   ```python
   BOT_TOKEN = "your_telegram_bot_token"
   ```
2. Simply double-click **`run.bat`** (or in terminal: `pip install -r requirements.txt` then `python bot.py`).
3. Open Telegram, search for your bot, send `/start`, and test!

---

## 🌐 Step 3: Push to GitHub

1. Create a **New Repository** on [GitHub](https://github.com/new) (e.g. `resume-maker-telegram-bot`).
2. In your terminal inside the `resume_maker_bot` folder, run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Resume Maker Bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/resume-maker-telegram-bot.git
   git push -u origin main
   ```

---

## 🚂 Step 4: Host 24/7 on Railway

1. Go to **[Railway.app](https://railway.app/)** and Log in with your **GitHub account**.
2. Click **"+ New Project"**.
3. Select **"Deploy from GitHub repo"**.
4. Choose your `resume-maker-telegram-bot` repository.
5. Click **"Deploy Now"**.
6. Once created, go to the **"Variables"** tab of your service and add:
   - **Variable Name:** `BOT_TOKEN`
   - **Value:** *(Paste your Telegram Bot Token from @BotFather)*
7. Railway will automatically build using `railway.json` / `Procfile` and start the bot!
8. Check **"Deploy Logs"** — you will see:
   ```
   🚀 Resume Maker Bot is running and ready for deployment!
   ```

---

## 📁 Project Structure

```
resume_maker_bot/
├── bot.py             # Main Telegram bot logic, wizard states & edit callbacks
├── config.py          # Bot configuration & color theme definitions
├── models.py          # Resume data structures & persistent JSON storage
├── pdf_generator.py   # ReportLab ATS-compliant PDF compiler with photo cropping
├── requirements.txt   # Python dependencies (python-telegram-bot, reportlab, pillow)
├── Procfile           # Process file for Railway / Heroku deployment
├── railway.json       # Railway automated deployment specification
├── run.bat            # 1-click local launcher for Windows
├── .gitignore         # Ignores temp files, uploads, and cached DBs
└── README.md          # Comprehensive deployment guide
```

