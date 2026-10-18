import os
import re
import logging
from typing import Dict, Any, List, Optional
from PIL import Image as PILImage, ImageOps, ImageDraw

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    HRFlowable,
    KeepTogether,
)

import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    import config
except ImportError:
    class FallbackConfig:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


def prepare_profile_photo(photo_path: str, size: int = 100) -> Optional[str]:
    """
    Processes the user profile photo:
    Crops to square, applies a circular mask with anti-aliasing,
    and saves as a high-quality temporary PNG.
    """
    if not photo_path or not os.path.exists(photo_path):
        return None

    try:
        with PILImage.open(photo_path) as img:
            img = img.convert("RGBA")
            # Fit square
            square_img = ImageOps.fit(img, (size * 2, size * 2), centering=(0.5, 0.5))

            # Create circular mask
            mask = PILImage.new("L", (size * 2, size * 2), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size * 2, size * 2), fill=255)

            # Circular cropped image
            circular_img = PILImage.new("RGBA", (size * 2, size * 2), (255, 255, 255, 0))
            circular_img.paste(square_img, (0, 0), mask=mask)

            # Save processed image
            out_path = f"{photo_path}_circle.png"
            circular_img.save(out_path, format="PNG")
            return out_path
    except Exception as e:
        logger.error(f"Error processing profile photo: {e}")
        return None


def clean_text(text: Optional[str]) -> str:
    """Escapes XML entities for ReportLab Paragraph rendering."""
    if not text:
        return ""
    cleaned = str(text)
    # Convert special chars to XML entities
    cleaned = cleaned.replace("&", "&amp;")
    cleaned = cleaned.replace("<", "&lt;")
    cleaned = cleaned.replace(">", "&gt;")
    return cleaned


def create_resume_pdf(user_id: int | str, data: Dict[str, Any]) -> str:
    """
    Generates a high-quality, ATS-compliant PDF resume from user data.
    Returns the absolute path to the generated PDF.
    """
    theme_key = data.get("theme", config.DEFAULT_THEME)
    theme = config.RESUME_THEMES.get(theme_key, config.RESUME_THEMES[config.DEFAULT_THEME])

    primary_color = HexColor(theme["primary"])
    secondary_color = HexColor(theme["secondary"])
    text_color = HexColor(theme["text"])
    muted_color = HexColor(theme["muted"])
    line_color = HexColor(theme["line"])

    clean_name = re.sub(r"[^\w\-_]", "_", str(data.get("name") or "User").strip())
    pdf_filename = f"Resume_{clean_name}_{user_id}.pdf"
    pdf_path = os.path.join(config.OUTPUT_DIR, pdf_filename)

    # Document setup with standard 0.5 inch (36 pt) margins for ATS layout
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=primary_color,
    )

    title_style = ParagraphStyle(
        "ResumeTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=secondary_color,
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=muted_color,
    )

    section_heading_style = ParagraphStyle(
        "ResumeSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        alignment=TA_LEFT,
    )

    body_bold = ParagraphStyle(
        "ResumeBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    muted_italic = ParagraphStyle(
        "ResumeMutedItalic",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        textColor=muted_color,
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    )

    story = []

    # =========================================================================
    # 1. HEADER SECTION (Name, Headline, Contact, and Optional Photo)
    # =========================================================================
    name = clean_text(data.get("name") or "Your Name")
    job_title = clean_text(data.get("title") or "")
    email = clean_text(data.get("email") or "")
    phone = clean_text(data.get("phone") or "")
    location = clean_text(data.get("location") or "")
    linkedin = clean_text(data.get("linkedin") or "")
    portfolio = clean_text(data.get("portfolio") or "")

    contact_items = []
    if email:
        contact_items.append(f"✉️ {email}")
    if phone:
        contact_items.append(f"📞 {phone}")
    if location:
        contact_items.append(f"📍 {location}")
    if linkedin:
        contact_items.append(f"🔗 {linkedin}")
    if portfolio:
        contact_items.append(f"🌐 {portfolio}")

    contact_line = " &nbsp;|&nbsp; ".join(contact_items)

    header_flowables = [
        Paragraph(name, name_style),
    ]
    if job_title:
        header_flowables.append(Spacer(1, 2))
        header_flowables.append(Paragraph(job_title.upper(), title_style))

    if contact_line:
        header_flowables.append(Spacer(1, 4))
        header_flowables.append(Paragraph(contact_line, contact_style))

    # Profile photo check
    photo_file = data.get("photo")
    processed_photo = prepare_profile_photo(photo_file, size=85) if photo_file else None

    if processed_photo and os.path.exists(processed_photo):
        # 2-column table: Left details, Right circular photo
        photo_img = RLImage(processed_photo, width=72, height=72)
        header_table = Table(
            [[header_flowables, photo_img]],
            colWidths=[460, 80]
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
    else:
        # Full width header
        for f in header_flowables:
            story.append(f)

    # Decorative Section Divider
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=8, spaceBefore=2))

    # Helper function for Section Headers
    def add_section_header(title: str):
        story.append(Paragraph(title.upper(), section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=line_color, spaceAfter=6, spaceBefore=2))

    # =========================================================================
    # 2. PROFESSIONAL SUMMARY / BACKGROUND
    # =========================================================================
    summary = clean_text(data.get("summary") or "").strip()
    if summary:
        add_section_header("Professional Summary")
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 6))

    # =========================================================================
    # 3. CORE COMPETENCIES / SKILLS
    # =========================================================================
    skills = data.get("skills", [])
    if skills:
        add_section_header("Core Competencies & Skills")

        # Clean list of skills
        clean_skills = [clean_text(s).strip() for s in skills if s and str(s).strip()]
        if clean_skills:
            # Render skills in an ATS-friendly bullet / badge table format (3 columns)
            cols = 3
            rows = []
            cur_row = []
            for s in clean_skills:
                cur_row.append(Paragraph(f"• &nbsp;<b>{s}</b>", body_style))
                if len(cur_row) == cols:
                    rows.append(cur_row)
                    cur_row = []
            if cur_row:
                while len(cur_row) < cols:
                    cur_row.append(Paragraph("", body_style))
                rows.append(cur_row)

            skills_table = Table(rows, colWidths=[180, 180, 180])
            skills_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(skills_table)
            story.append(Spacer(1, 6))

    # =========================================================================
    # 4. WORK EXPERIENCE
    # =========================================================================
    experiences = data.get("experience", [])
    if experiences:
        add_section_header("Professional Experience")

        for exp in experiences:
            exp_flow = []
            r_title = clean_text(exp.get("title") or "Role")
            company = clean_text(exp.get("company") or "")
            duration = clean_text(exp.get("duration") or "")
            loc = clean_text(exp.get("location") or "")
            details = exp.get("details") or ""

            # Top Row: Role Title (Left) + Duration (Right)
            left_text = f"<b>{r_title}</b>"
            if company:
                left_text += f" &nbsp;|&nbsp; <font color='{secondary_color.hexval()}'>{company}</font>"
            if loc:
                left_text += f" <font color='{muted_color.hexval()}'>({loc})</font>"

            exp_table = Table(
                [[Paragraph(left_text, body_style), Paragraph(duration, TA_RIGHT and ParagraphStyle("ExpDur", parent=muted_italic, alignment=TA_RIGHT))]],
                colWidths=[400, 140]
            )
            exp_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            exp_flow.append(exp_table)

            # Bullet points / description
            if details:
                # If user entered multi-line or bullet items, split by newline
                lines = [d.strip() for d in str(details).split("\n") if d.strip()]
                for l in lines:
                    clean_l = clean_text(l).lstrip("•-* ").strip()
                    if clean_l:
                        exp_flow.append(Paragraph(f"• &nbsp;{clean_l}", bullet_style))

            exp_flow.append(Spacer(1, 6))
            story.append(KeepTogether(exp_flow))

    # =========================================================================
    # 5. EDUCATION
    # =========================================================================
    education = data.get("education", [])
    if education:
        add_section_header("Education")

        for edu in education:
            edu_flow = []
            degree = clean_text(edu.get("degree") or "Degree")
            institution = clean_text(edu.get("institution") or "")
            year = clean_text(edu.get("year") or "")
            score = clean_text(edu.get("score") or "")

            left_edu = f"<b>{degree}</b>"
            if institution:
                left_edu += f" &nbsp;|&nbsp; <font color='{secondary_color.hexval()}'>{institution}</font>"
            if score:
                left_edu += f" &nbsp;•&nbsp; <font color='{text_color.hexval()}'>Score: {score}</font>"

            edu_table = Table(
                [[Paragraph(left_edu, body_style), Paragraph(year, ParagraphStyle("EduYr", parent=muted_italic, alignment=TA_RIGHT))]],
                colWidths=[430, 110]
            )
            edu_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            edu_flow.append(edu_table)
            edu_flow.append(Spacer(1, 4))
            story.append(KeepTogether(edu_flow))

    # =========================================================================
    # 6. CERTIFICATIONS & LICENSES
    # =========================================================================
    certifications = data.get("certifications", [])
    if certifications:
        add_section_header("Certifications & Licenses")

        for cert in certifications:
            cert_flow = []
            c_name = clean_text(cert.get("name") or "Certification")
            issuer = clean_text(cert.get("issuer") or "")
            c_year = clean_text(cert.get("year") or "")

            left_cert = f"• &nbsp;<b>{c_name}</b>"
            if issuer:
                left_cert += f" &nbsp;—&nbsp; <font color='{secondary_color.hexval()}'>{issuer}</font>"

            cert_table = Table(
                [[Paragraph(left_cert, body_style), Paragraph(c_year, ParagraphStyle("CertYr", parent=muted_italic, alignment=TA_RIGHT))]],
                colWidths=[450, 90]
            )
            cert_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            cert_flow.append(cert_table)
            cert_flow.append(Spacer(1, 3))
            story.append(KeepTogether(cert_flow))

    # Build PDF
    doc.build(story)
    logger.info(f"Generated PDF Resume successfully at: {pdf_path}")
    return pdf_path

