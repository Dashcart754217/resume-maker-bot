import os
import sys
import logging
from typing import Dict, Any

# Ensure current directory is in sys.path for Railway / Linux containers
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Resilient config import with fallback if config.py was omitted on GitHub
try:
    import config
except ImportError:
    class FallbackConfig:
        BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
        OUTPUT_DIR = os.path.join(BASE_DIR, "resumes")
        DEFAULT_THEME = "navy"
        RESUME_THEMES = {
            "navy": {
                "name": "👔 Modern Navy",
                "primary": "#1A365D",
                "secondary": "#2B6CB0",
                "text": "#2D3748",
                "muted": "#718096",
                "line": "#E2E8F0",
                "tag_bg": "#EDF2F7",
            },
            "emerald": {
                "name": "🌲 Executive Emerald",
                "primary": "#1C4532",
                "secondary": "#276749",
                "text": "#2D3748",
                "muted": "#718096",
                "line": "#E2E8F0",
                "tag_bg": "#F0FFF4",
            },
            "charcoal": {
                "name": "🖤 Classic Charcoal (ATS Favorite)",
                "primary": "#1A202C",
                "secondary": "#4A5568",
                "text": "#2D3748",
                "muted": "#718096",
                "line": "#CBD5E0",
                "tag_bg": "#EDF2F7",
            },
            "burgundy": {
                "name": "🍷 Royal Burgundy",
                "primary": "#5E1724",
                "secondary": "#9B2C2C",
                "text": "#2D3748",
                "muted": "#718096",
                "line": "#E2E8F0",
                "tag_bg": "#FFF5F5",
            }
        }
    config = FallbackConfig()
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

from models import resume_store
from pdf_generator import create_resume_pdf

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# =============================================================================
# KEYBOARDS & HELPERS
# =============================================================================
def skip_cancel_keyboard(skip_cb: str = "skip_step") -> InlineKeyboardMarkup:
    """Returns an inline keyboard with a Skip and a Cancel button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭️ Skip this step", callback_data=skip_cb)],
        [InlineKeyboardButton("❌ Main Menu", callback_data="main_menu")]
    ])


def dashboard_keyboard(user_id: int | str) -> InlineKeyboardMarkup:
    """Main dashboard keyboard with 1-click edit buttons and PDF generator."""
    data = resume_store.get(user_id)
    cur_theme = data.get("theme", config.DEFAULT_THEME)
    theme_name = config.RESUME_THEMES.get(cur_theme, {}).get("name", "Navy")

    buttons = [
        [InlineKeyboardButton("📄 Generate PDF Resume 🚀", callback_data="generate_pdf")],
        [InlineKeyboardButton(f"🎨 Theme: {theme_name}", callback_data="change_theme")],
        [
            InlineKeyboardButton("✏️ Name & Title", callback_data="edit_name"),
            InlineKeyboardButton("✏️ Contact Info", callback_data="edit_contact"),
        ],
        [
            InlineKeyboardButton("✏️ Summary", callback_data="edit_summary"),
            InlineKeyboardButton("✏️ Skills", callback_data="edit_skills"),
        ],
        [
            InlineKeyboardButton("✏️ Experience", callback_data="edit_experience"),
            InlineKeyboardButton("✏️ Education", callback_data="edit_education"),
        ],
        [
            InlineKeyboardButton("✏️ Certifications", callback_data="edit_certs"),
            InlineKeyboardButton("📸 Change Photo", callback_data="edit_photo"),
        ],
        [
            InlineKeyboardButton("🔄 Reset & Start Fresh", callback_data="confirm_reset"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


# =============================================================================
# START & MAIN MENU
# =============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome greeting and navigation menu."""
    user = update.effective_user
    resume_data = resume_store.get(user.id)
    resume_data["state"] = None
    resume_store.save()

    has_data = bool(resume_data.get("name"))

    text = (
        f"👋 <b>Namaste {user.first_name}! Welcome to Resume Maker Bot</b> 📄✨\n\n"
        f"Yeh bot aapke liye <b>Professional, Job-Ready aur ATS-Compliant PDF Resume</b> "
        f"banakar dega — kuch hi minutes mein!\n\n"
        f"🌟 <b>Key Features:</b>\n"
        f"• 📸 Profile Photo Upload (Circle frame)\n"
        f"• 💼 Experience, Education, Skills, Summary & Certifications\n"
        f"• ⏭️ <b>Har step par Skip option</b> (kuch nahi daalna toh skip karein)\n"
        f"• ✏️ <b>Easy Edit Feature</b> (kisi bhi waqt koi bhi section update karein)\n"
        f"• 🎨 4 Modern Color Themes (Navy, Emerald, Charcoal, Burgundy)\n\n"
        f"👉 Shuru karne ke liye neeche button dabayein:"
    )

    buttons = []
    if has_data:
        buttons.append([InlineKeyboardButton("📋 View & Edit Current Resume", callback_data="view_dashboard")])
        buttons.append([InlineKeyboardButton("📄 Re-download PDF Resume", callback_data="generate_pdf")])
        buttons.append([InlineKeyboardButton("🚀 Start Fresh / New Resume", callback_data="start_wizard")])
    else:
        buttons.append([InlineKeyboardButton("🚀 Start Creating My Resume", callback_data="start_wizard")])

    buttons.append([InlineKeyboardButton("ℹ️ Help & Tips", callback_data="help_menu")])

    reply_markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Provides usage guidance."""
    query = update.callback_query
    await query.answer()

    text = (
        "📖 <b>How to Use Resume Maker Bot:</b>\n\n"
        "1. <b>Step-by-step Wizard:</b> Bot aapse photo, name, experience, education poochhega.\n"
        "2. <b>Skip Anything:</b> Agar koi section aapke paas nahi hai (jaise Photo ya Certification), "
        "toh <code>⏭️ Skip this step</code> button dabayein ya <code>/skip</code> type karein.\n"
        "3. <b>Dashboard & Edit:</b> Poora data bharne ke baad ek dashboard khulega jahan se aap "
        "kisi bhi information ko modify kar sakte hain.\n"
        "4. <b>Download PDF:</b> 'Generate PDF' dabate hi aapko aapka ATS-ready resume file bhej di jayegi.\n\n"
        "Commands:\n"
        "• /start - Main Menu\n"
        "• /resume - Open Resume Dashboard\n"
        "• /skip - Skip current prompt\n"
        "• /cancel - Cancel & return to menu"
    )
    kb = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


# =============================================================================
# WIZARD FLOW (STEP-BY-STEP)
# =============================================================================
async def start_wizard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the sequential wizard beginning with photo upload."""
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id
    resume_store.reset(user_id)
    resume_data = resume_store.get(user_id)
    resume_data["state"] = "WAITING_PHOTO"
    resume_store.save()

    text = (
        "📸 <b>Step 1/9: Profile Photo</b>\n\n"
        "Kripya apni ek professional headshot photo upload karein (PNG / JPG format mein).\n\n"
        "💡 <i>Photo circular crop hokar resume ke top corner par lagegi. Agar photo nahi lagani, toh 'Skip' dabayein!</i>"
    )
    kb = skip_cancel_keyboard("skip_photo")
    if query:
        await query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Full Name."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_NAME")

    text = (
        "👤 <b>Step 2/9: Full Name</b>\n\n"
        "Apna poora naam (Full Name) enter karein jo resume ke top par sabse bada dikhega:\n"
        "<i>Example: Rahul Sharma</i>"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="main_menu")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Target Job Title / Headline."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_TITLE")

    text = (
        "💼 <b>Step 3/9: Professional Title / Headline</b>\n\n"
        "Aapka target job role ya current profession kya hai?\n"
        "<i>Examples: Senior Software Engineer | Digital Marketing Specialist | Fresh Graduate</i>"
    )
    kb = skip_cancel_keyboard("skip_title")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Contact Info (Email, Phone, Location)."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_CONTACT")

    text = (
        "📞 <b>Step 4/9: Contact Information</b>\n\n"
        "Kripya apna <b>Email</b>, <b>Phone Number</b>, aur <b>City / Location</b> enter karein.\n\n"
        "📝 <i>Format example (single message ya separate lines):</i>\n"
        "<code>rahul.sharma@example.com\n+91 98765 43210\nNew Delhi, India\nlinkedin.com/in/rahulsharma</code>"
    )
    kb = skip_cancel_keyboard("skip_contact")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Professional Summary / Background."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_SUMMARY")

    text = (
        "📝 <b>Step 5/9: Professional Summary / Background</b>\n\n"
        "Apne career ke baare mein 2-4 lines ka summary likhein jo recruiter ko impress kare:\n\n"
        "<i>Example: Results-driven Software Developer with 3+ years of experience building scalable web applications. Passionate about clean code, performance optimization, and agile teamwork.</i>"
    )
    kb = skip_cancel_keyboard("skip_summary")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Core Competencies / Skills."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_SKILLS")

    text = (
        "🛠️ <b>Step 6/9: Core Competencies & Skills</b>\n\n"
        "Apni technical aur soft skills comma (,) se separate karke enter karein:\n\n"
        "<i>Example: Python, Django, PostgreSQL, Docker, Git, REST APIs, Team Leadership, Problem Solving</i>"
    )
    kb = skip_cancel_keyboard("skip_skills")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Work Experience."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_EXP_ROLE", temp_item={})

    text = (
        "💼 <b>Step 7/9: Professional Work Experience</b>\n\n"
        "Apni job position / role aur company enter karein:\n\n"
        "<i>Example: Software Engineer at Infosys, Bangalore</i>\n\n"
        "💡 <i>Agar aap Fresher hain ya experience nahi jodna chahte, toh 'Skip' dabayein!</i>"
    )
    kb = skip_cancel_keyboard("skip_experience")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Education."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_EDU_DEGREE", temp_item={})

    text = (
        "🎓 <b>Step 8/9: Education Details</b>\n\n"
        "Apni highest degree aur college/school ka naam enter karein:\n\n"
        "<i>Example: B.Tech in Computer Science from Delhi University</i>"
    )
    kb = skip_cancel_keyboard("skip_education")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def prompt_certifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompts for Certifications & Licenses."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state="WAITING_CERTS")

    text = (
        "📜 <b>Step 9/9: Certifications & Training</b>\n\n"
        "Apne certifications ya licenses enter karein (har certification nayi line par ya comma se alag):\n\n"
        "<i>Example:\nAWS Certified Solutions Architect (2024)\nGoogle Data Analytics Professional Certificate (2023)</i>"
    )
    kb = skip_cancel_keyboard("skip_certs")
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# =============================================================================
# DASHBOARD / REVIEW SCREEN
# =============================================================================
async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str = None):
    """Displays the interactive overview and edit panel."""
    user_id = update.effective_user.id
    resume_store.update(user_id, state=None, edit_section=None)

    overview_text = resume_store.format_summary_text(user_id)
    if message_text:
        overview_text = f"{message_text}\n\n{overview_text}"

    kb = dashboard_keyboard(user_id)

    if update.callback_query:
        await update.callback_query.edit_message_text(overview_text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(overview_text, reply_markup=kb, parse_mode=ParseMode.HTML)


# =============================================================================
# PHOTO HANDLER
# =============================================================================
async def photo_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes headshot image uploads."""
    user = update.effective_user
    data = resume_store.get(user.id)
    cur_state = data.get("state")

    if cur_state not in ("WAITING_PHOTO", "EDIT_PHOTO"):
        return

    photo_file = await update.message.photo[-1].get_file()
    save_path = os.path.join(config.UPLOADS_DIR, f"user_{user.id}.jpg")
    await photo_file.download_to_drive(save_path)

    resume_store.update(user.id, photo=save_path)

    await update.message.reply_text("✅ <b>Photo successfully attached!</b>", parse_mode=ParseMode.HTML)

    if cur_state == "EDIT_PHOTO":
        await show_dashboard(update, context, "✅ <b>Photo updated successfully!</b>")
    else:
        await prompt_name(update, context)


# =============================================================================
# TEXT MESSAGE ROUTER (INPUT CAPTURE)
# =============================================================================
async def text_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes incoming text input based on the active wizard / edit state."""
    user_id = update.effective_user.id
    raw_text = update.message.text.strip()
    data = resume_store.get(user_id)
    state = data.get("state")
    edit_section = data.get("edit_section")

    if not state and not edit_section:
        await update.message.reply_text(
            "💡 Type /resume to open your Resume Dashboard or /start to begin a new one."
        )
        return

    # Handle Edit States
    if edit_section:
        await handle_edit_input(update, context, edit_section, raw_text)
        return

    # Standard Wizard Flow
    if state == "WAITING_NAME":
        resume_store.update(user_id, name=raw_text)
        await prompt_title(update, context)

    elif state == "WAITING_TITLE":
        resume_store.update(user_id, title=raw_text)
        await prompt_contact(update, context)

    elif state == "WAITING_CONTACT":
        parse_and_store_contact(user_id, raw_text)
        await prompt_summary(update, context)

    elif state == "WAITING_SUMMARY":
        resume_store.update(user_id, summary=raw_text)
        await prompt_skills(update, context)

    elif state == "WAITING_SKILLS":
        skills_list = [s.strip() for s in raw_text.replace("\n", ",").split(",") if s.strip()]
        resume_store.update(user_id, skills=skills_list)
        await prompt_experience(update, context)

    # --- Work Experience Multi-step sub-wizard ---
    elif state == "WAITING_EXP_ROLE":
        data["temp_item"] = {"title": raw_text}
        data["state"] = "WAITING_EXP_DURATION"
        resume_store.save()
        await update.message.reply_text(
            f"📅 Enter duration / years for <b>{raw_text}</b>:\n<i>Example: Jan 2022 - Present (or 2021 - 2023)</i>",
            reply_markup=skip_cancel_keyboard("skip_exp_duration"),
            parse_mode=ParseMode.HTML
        )

    elif state == "WAITING_EXP_DURATION":
        data["temp_item"]["duration"] = raw_text
        data["state"] = "WAITING_EXP_DETAILS"
        resume_store.save()
        await update.message.reply_text(
            "📋 Enter key responsibilities / achievements (you can write multiple bullet lines):\n"
            "<i>Example:\n- Built REST APIs serving 50k users\n- Improved page load speed by 35%</i>",
            reply_markup=skip_cancel_keyboard("skip_exp_details"),
            parse_mode=ParseMode.HTML
        )

    elif state == "WAITING_EXP_DETAILS":
        data["temp_item"]["details"] = raw_text
        exp_list = data.get("experience", [])
        exp_list.append(data["temp_item"])
        data["experience"] = exp_list
        data["temp_item"] = {}
        resume_store.save()

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Another Experience", callback_data="add_another_exp")],
            [InlineKeyboardButton("✅ Done with Experience (Next)", callback_data="skip_experience")]
        ])
        await update.message.reply_text(
            f"✅ <b>Experience saved!</b> (Total: {len(exp_list)})\nDo you want to add another experience?",
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )

    # --- Education Multi-step sub-wizard ---
    elif state == "WAITING_EDU_DEGREE":
        data["temp_item"] = {"degree": raw_text}
        data["state"] = "WAITING_EDU_YEAR"
        resume_store.save()
        await update.message.reply_text(
            f"📅 Enter passing year and score/GPA for <b>{raw_text}</b>:\n<i>Example: 2023 | 8.8 CGPA (or just 2022)</i>",
            reply_markup=skip_cancel_keyboard("skip_edu_year"),
            parse_mode=ParseMode.HTML
        )

    elif state == "WAITING_EDU_YEAR":
        data["temp_item"]["year"] = raw_text
        edu_list = data.get("education", [])
        edu_list.append(data["temp_item"])
        data["education"] = edu_list
        data["temp_item"] = {}
        resume_store.save()

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Another Education", callback_data="add_another_edu")],
            [InlineKeyboardButton("✅ Done with Education (Next)", callback_data="skip_education")]
        ])
        await update.message.reply_text(
            f"✅ <b>Education saved!</b> (Total: {len(edu_list)})\nDo you want to add another degree/school?",
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )

    # --- Certifications ---
    elif state == "WAITING_CERTS":
        cert_lines = [c.strip() for c in raw_text.split("\n") if c.strip()]
        certs = []
        for c in cert_lines:
            certs.append({"name": c, "issuer": "", "year": ""})
        resume_store.update(user_id, certifications=certs)

        await show_dashboard(update, context, "🎉 <b>All steps completed! Here is your resume preview:</b>")


def parse_and_store_contact(user_id: int | str, text: str):
    """Parses contact info from text block."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    data = resume_store.get(user_id)

    email = ""
    phone = ""
    location = ""
    linkedin = ""

    for l in lines:
        if "@" in l and "." in l and not email:
            email = l
        elif any(c.isdigit() for c in l) and len([c for c in l if c.isdigit()]) >= 8 and not phone:
            phone = l
        elif "linkedin.com" in l.lower():
            linkedin = l
        elif not location:
            location = l

    data["email"] = email or lines[0] if lines else ""
    if len(lines) > 1 and not phone:
        data["phone"] = lines[1]
    elif phone:
        data["phone"] = phone
    if location:
        data["location"] = location
    if linkedin:
        data["linkedin"] = linkedin
    resume_store.save()


# =============================================================================
# EDIT SECTION HANDLERS
# =============================================================================
async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE, section: str, text: str):
    """Updates a single section and returns straight to the dashboard."""
    user_id = update.effective_user.id
    data = resume_store.get(user_id)

    if section == "edit_name":
        lines = text.split("\n")
        data["name"] = lines[0].strip()
        if len(lines) > 1:
            data["title"] = lines[1].strip()

    elif section == "edit_contact":
        parse_and_store_contact(user_id, text)

    elif section == "edit_summary":
        data["summary"] = text

    elif section == "edit_skills":
        data["skills"] = [s.strip() for s in text.replace("\n", ",").split(",") if s.strip()]

    elif section == "edit_experience":
        # Formats lines into experience
        exp_entries = []
        blocks = text.split("\n\n")
        for b in blocks:
            blines = [x.strip() for x in b.split("\n") if x.strip()]
            if blines:
                role = blines[0]
                dur = blines[1] if len(blines) > 1 else ""
                desc = "\n".join(blines[2:]) if len(blines) > 2 else ""
                exp_entries.append({"title": role, "duration": dur, "details": desc})
        data["experience"] = exp_entries

    elif section == "edit_education":
        edu_entries = []
        for line in text.split("\n"):
            if line.strip():
                edu_entries.append({"degree": line.strip()})
        data["education"] = edu_entries

    elif section == "edit_certs":
        certs = []
        for line in text.split("\n"):
            if line.strip():
                certs.append({"name": line.strip()})
        data["certifications"] = certs

    resume_store.update(user_id, edit_section=None, state=None)
    await show_dashboard(update, context, "✅ <b>Section updated successfully!</b>")


# =============================================================================
# CALLBACK QUERY ROUTER (BUTTON CLICKS)
# =============================================================================
async def callback_query_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dispatches button clicks."""
    query = update.callback_query
    data_cb = query.data
    user_id = update.effective_user.id
    user_resume = resume_store.get(user_id)

    # 1. Main Navigation
    if data_cb == "main_menu":
        await query.answer()
        await start_command(update, context)

    elif data_cb == "view_dashboard":
        await query.answer()
        await show_dashboard(update, context)

    elif data_cb == "help_menu":
        await help_menu(update, context)

    elif data_cb == "start_wizard":
        await start_wizard(update, context)

    # 2. Skip Buttons for every step
    elif data_cb == "skip_photo":
        await query.answer("Photo skipped")
        user_resume["photo"] = None
        await prompt_name(update, context)

    elif data_cb == "skip_title":
        await query.answer("Title skipped")
        user_resume["title"] = ""
        await prompt_contact(update, context)

    elif data_cb == "skip_contact":
        await query.answer("Contact skipped")
        await prompt_summary(update, context)

    elif data_cb == "skip_summary":
        await query.answer("Summary skipped")
        user_resume["summary"] = ""
        await prompt_skills(update, context)

    elif data_cb == "skip_skills":
        await query.answer("Skills skipped")
        user_resume["skills"] = []
        await prompt_experience(update, context)

    elif data_cb == "skip_exp_duration":
        await query.answer("Duration skipped")
        user_resume["state"] = "WAITING_EXP_DETAILS"
        resume_store.save()
        await query.message.reply_text(
            "📋 Enter key responsibilities / achievements (or Skip):",
            reply_markup=skip_cancel_keyboard("skip_exp_details"),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "skip_exp_details":
        await query.answer("Details skipped")
        exp_list = user_resume.get("experience", [])
        if user_resume.get("temp_item"):
            exp_list.append(user_resume["temp_item"])
            user_resume["experience"] = exp_list
            user_resume["temp_item"] = {}
        resume_store.save()
        await prompt_education(update, context)

    elif data_cb in ("skip_experience", "skip_exp"):
        await query.answer("Experience skipped/finished")
        await prompt_education(update, context)

    elif data_cb == "add_another_exp":
        await query.answer()
        user_resume["state"] = "WAITING_EXP_ROLE"
        user_resume["temp_item"] = {}
        resume_store.save()
        await query.message.reply_text(
            "💼 Enter next Job Role / Title & Company:\n<i>Example: Frontend Developer at TCS</i>",
            reply_markup=skip_cancel_keyboard("skip_experience"),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "skip_edu_year":
        await query.answer("Year skipped")
        edu_list = user_resume.get("education", [])
        if user_resume.get("temp_item"):
            edu_list.append(user_resume["temp_item"])
            user_resume["education"] = edu_list
            user_resume["temp_item"] = {}
        resume_store.save()
        await prompt_certifications(update, context)

    elif data_cb == "add_another_edu":
        await query.answer()
        user_resume["state"] = "WAITING_EDU_DEGREE"
        user_resume["temp_item"] = {}
        resume_store.save()
        await query.message.reply_text(
            "🎓 Enter next Degree / School details:\n<i>Example: Class 12 CBSE (PCM) - 92%</i>",
            reply_markup=skip_cancel_keyboard("skip_education"),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "skip_education":
        await query.answer("Education skipped/finished")
        await prompt_certifications(update, context)

    elif data_cb == "skip_certs":
        await query.answer("Certifications skipped")
        user_resume["certifications"] = []
        await show_dashboard(update, context, "🎉 <b>Resume information captured! Here is your dashboard:</b>")

    # 3. Edit Individual Sections
    elif data_cb == "edit_name":
        await query.answer()
        user_resume["edit_section"] = "edit_name"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Name & Title:</b>\n\nApna naya Full Name aur Headline bhejein:\n"
            "<code>Rahul Sharma\nSenior Data Scientist</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_contact":
        await query.answer()
        user_resume["edit_section"] = "edit_contact"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Contact Info:</b>\n\nNaya email, phone, location bhejein:\n"
            "<code>rahul@gmail.com\n+91 9876543210\nMumbai, India</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_summary":
        await query.answer()
        user_resume["edit_section"] = "edit_summary"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Professional Summary:</b>\n\nNaya summary paragraph bhejein:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_skills":
        await query.answer()
        user_resume["edit_section"] = "edit_skills"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Skills:</b>\n\nComma-separated updated skills bhejein:\n"
            "<i>Python, React, AWS, Docker, Machine Learning</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_experience":
        await query.answer()
        user_resume["edit_section"] = "edit_experience"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Experience:</b>\n\nApni saari job experiences format me bhejein:\n\n"
            "<code>Senior Developer at Wipro\n2022 - Present\n- Led development of microservices\n- Mentored junior devs\n\nJunior Engineer at TechCorp\n2020 - 2022\n- Developed UI components</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_education":
        await query.answer()
        user_resume["edit_section"] = "edit_education"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Education:</b>\n\nApni degree details bhejein (har degree nayi line par):\n"
            "<code>B.Tech Computer Science - IIT Bombay (2020-2024)\nClass 12 CBSE - 95% (2020)</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_certs":
        await query.answer()
        user_resume["edit_section"] = "edit_certs"
        resume_store.save()
        await query.message.reply_text(
            "✏️ <b>Edit Certifications:</b>\n\nCertifications ki list bhejein (one per line):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel Edit", callback_data="view_dashboard")]]),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "edit_photo":
        await query.answer()
        user_resume["state"] = "EDIT_PHOTO"
        resume_store.save()
        kb = [
            [InlineKeyboardButton("🗑️ Remove Current Photo", callback_data="remove_photo")],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="view_dashboard")]
        ]
        await query.message.reply_text(
            "📸 <b>Update Profile Photo:</b>\n\nNayi photo bhejein ya neeche se remove karein:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "remove_photo":
        await query.answer("Photo removed!")
        user_resume["photo"] = None
        user_resume["state"] = None
        resume_store.save()
        await show_dashboard(update, context, "✅ <b>Photo removed from resume!</b>")

    # 4. Color Theme Selection
    elif data_cb == "change_theme":
        await query.answer()
        theme_buttons = []
        for tk, tv in config.RESUME_THEMES.items():
            theme_buttons.append([InlineKeyboardButton(tv["name"], callback_data=f"set_theme_{tk}")])
        theme_buttons.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="view_dashboard")])
        await query.edit_message_text(
            "🎨 <b>Choose a Professional Theme for your Resume:</b>\n\n"
            "Har theme ATS-compliant aur clean fonts & divider lines use karta hai.",
            reply_markup=InlineKeyboardMarkup(theme_buttons),
            parse_mode=ParseMode.HTML
        )

    elif data_cb.startswith("set_theme_"):
        new_theme = data_cb.replace("set_theme_", "")
        user_resume["theme"] = new_theme
        resume_store.save()
        theme_name = config.RESUME_THEMES.get(new_theme, {}).get("name", new_theme)
        await query.answer(f"Theme changed to {theme_name}!")
        await show_dashboard(update, context, f"🎨 <b>Theme updated to {theme_name}!</b>")

    # 5. Reset Confirmation
    elif data_cb == "confirm_reset":
        await query.answer()
        kb = [
            [InlineKeyboardButton("⚠️ Yes, Reset Everything", callback_data="do_reset")],
            [InlineKeyboardButton("❌ No, Keep My Resume", callback_data="view_dashboard")]
        ]
        await query.edit_message_text(
            "⚠️ <b>Kya aap apna saara data reset karna chahte hain?</b>\n\nAapka purana resume delete ho jayega.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.HTML
        )

    elif data_cb == "do_reset":
        await query.answer("Resume reset!")
        resume_store.reset(user_id)
        await start_wizard(update, context)

    # 6. PDF Generation & Delivery
    elif data_cb == "generate_pdf":
        await handle_generate_pdf(update, context)


async def handle_generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates the PDF resume and sends it as a document."""
    query = update.callback_query
    if query:
        await query.answer("Generating your PDF resume...", show_alert=False)

    user_id = update.effective_user.id
    data = resume_store.get(user_id)

    if not data.get("name"):
        text = "⚠️ <b>Pehle apna resume create karein!</b>\nNeeche button dabakar shuru karein:"
        kb = [[InlineKeyboardButton("🚀 Start Creating Resume", callback_data="start_wizard")]]
        if query:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        return

    status_msg = await update.effective_chat.send_message(
        "⏳ <b>Designing & compiling your ATS-friendly PDF Resume...</b>",
        parse_mode=ParseMode.HTML
    )

    try:
        pdf_path = create_resume_pdf(user_id, data)
        file_size_kb = round(os.path.getsize(pdf_path) / 1024, 1)

        theme_name = config.RESUME_THEMES.get(data.get("theme", "navy"), {}).get("name", "Navy")
        caption = (
            f"🎉 <b>Aapka Professional Resume PDF Taiyar Hai!</b>\n\n"
            f"👤 <b>Name:</b> {data.get('name')}\n"
            f"💼 <b>Target:</b> {data.get('title') or 'Job Applicant'}\n"
            f"🎨 <b>Theme:</b> {theme_name}\n"
            f"📦 <b>Size:</b> {file_size_kb} KB\n\n"
            f"✨ <i>100% ATS Friendly & Ready for Job Applications!</i>"
        )

        action_kb = [
            [InlineKeyboardButton("✏️ Edit Resume Details", callback_data="view_dashboard")],
            [InlineKeyboardButton("🎨 Change Theme & Re-download", callback_data="change_theme")],
            [InlineKeyboardButton("🔄 Create Another Resume", callback_data="confirm_reset")]
        ]

        with open(pdf_path, "rb") as f:
            await update.effective_chat.send_document(
                document=f,
                filename=os.path.basename(pdf_path),
                caption=caption,
                reply_markup=InlineKeyboardMarkup(action_kb),
                parse_mode=ParseMode.HTML
            )

        await status_msg.delete()

    except Exception as e:
        logger.exception("Error generating resume PDF")
        await status_msg.edit_text(
            f"❌ <b>Error creating PDF:</b>\n<code>{str(e)}</code>\n\nPlease try again or contact admin.",
            parse_mode=ParseMode.HTML
        )


# =============================================================================
# SKIP COMMAND & BOT INITIALIZATION
# =============================================================================
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler for typed /skip."""
    user_id = update.effective_user.id
    data = resume_store.get(user_id)
    state = data.get("state")

    if state == "WAITING_PHOTO":
        await prompt_name(update, context)
    elif state == "WAITING_TITLE":
        await prompt_contact(update, context)
    elif state == "WAITING_CONTACT":
        await prompt_summary(update, context)
    elif state == "WAITING_SUMMARY":
        await prompt_skills(update, context)
    elif state == "WAITING_SKILLS":
        await prompt_experience(update, context)
    elif state in ("WAITING_EXP_ROLE", "WAITING_EXP_DURATION", "WAITING_EXP_DETAILS"):
        await prompt_education(update, context)
    elif state in ("WAITING_EDU_DEGREE", "WAITING_EDU_YEAR"):
        await prompt_certifications(update, context)
    elif state == "WAITING_CERTS":
        await show_dashboard(update, context)
    else:
        await update.message.reply_text("Nothing to skip right now. Type /resume to see your dashboard.")


def main():
    """Initializes and runs the Telegram Bot."""
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("=" * 60)
        print("⚠️  ERROR: BOT_TOKEN is not configured!")
        print("Please set the BOT_TOKEN environment variable in Railway")
        print("or edit config.py with your token from @BotFather.")
        print("=" * 60)
        return

    application = Application.builder().token(config.BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", start_command))
    application.add_handler(CommandHandler("resume", show_dashboard))
    application.add_handler(CommandHandler("generate", handle_generate_pdf))
    application.add_handler(CommandHandler("skip", skip_command))
    application.add_handler(CommandHandler("cancel", start_command))

    # Callbacks (Buttons)
    application.add_handler(CallbackQueryHandler(callback_query_router))

    # Photo & Text messages
    application.add_handler(MessageHandler(filters.PHOTO, photo_message_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_router))

    print("🚀 Resume Maker Bot is running and ready for deployment!")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

