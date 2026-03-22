import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.platypus import Image as RLImage
import io
import re
import requests
import tempfile
import os

# --- OpenAI Client ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="MythosForge AI",
    page_icon="⚡",
    layout="centered"
)

# -------------------------------------------------------
# CUSTOM CSS
# -------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Full page — parchment texture via CSS noise pattern */
.stApp {
    background-color: #f5f0e8;
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23noise)' opacity='0.035'/%3E%3C/svg%3E");
    background-repeat: repeat;
}

/* ---- HERO ---- */
.hero {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 50%, #0d0d1a 100%);
    padding: 60px 40px 50px 40px;
    text-align: center;
    border-radius: 0 0 30px 30px;
    margin: -60px -60px 40px -60px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    position: relative;
    overflow: hidden;
}

/* Subtle radial glow behind title */
.hero::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 500px;
    height: 200px;
    background: radial-gradient(ellipse, rgba(232,200,122,0.08) 0%, transparent 70%);
    pointer-events: none;
}

.hero-title {
    font-family: 'Cinzel', serif;
    font-size: 3em;
    font-weight: 700;
    color: #e8c87a;
    letter-spacing: 4px;
    margin: 0;
    text-shadow: 0 0 30px rgba(232,200,122,0.5);
}

.hero-subtitle {
    font-family: 'Lato', sans-serif;
    font-size: 1.1em;
    color: #a89bc2;
    margin-top: 10px;
    letter-spacing: 2px;
    font-weight: 300;
}

/* ---- GOLDEN SEPARATOR ---- */
.hero-divider {
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #e8c87a, transparent);
    margin: 20px auto;
}

/* ---- EPIC TAGLINE ---- */
.hero-tagline {
    font-family: 'Cinzel', serif;
    font-size: 0.78em;
    color: #e8c87a;
    opacity: 0.6;
    letter-spacing: 3px;
    margin-top: 18px;
    font-style: italic;
}

/* ---- FORM CARD with parchment texture ---- */
.form-card {
    background-color: #fffdf7;
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E"),
        linear-gradient(160deg, #fffef9 0%, #fdf6e3 50%, #faf0d7 100%);
    background-repeat: repeat, no-repeat;
    background-size: 300px 300px, cover;
    border-radius: 16px;
    padding: 35px 40px;
    box-shadow:
        0 4px 24px rgba(0,0,0,0.07),
        inset 0 1px 0 rgba(255,255,255,0.8);
    margin-bottom: 24px;
    border: 1px solid #e2d9c5;
}

.section-label {
    font-family: 'Cinzel', serif;
    font-size: 0.85em;
    color: #4B0082;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
    font-weight: 700;
}

/* ---- INPUT FIELDS ---- */
.stTextInput > div > div > input {
    background: #ffffff !important;
    border: 1.5px solid #c9bca8 !important;
    border-radius: 10px !important;
    font-family: 'Lato', sans-serif !important;
    font-size: 1em !important;
    color: #1a1a1a !important;
    padding: 12px 16px !important;
}

.stTextArea > div > div > textarea {
    background: #ffffff !important;
    border: 1.5px solid #c9bca8 !important;
    border-radius: 10px !important;
    font-family: 'Lato', sans-serif !important;
    font-size: 1em !important;
    color: #1a1a1a !important;
    padding: 12px 16px !important;
}

/* Placeholder text color */
.stTextInput > div > div > input::placeholder {
    color: #9e8f7a !important;
    opacity: 1 !important;
}

.stTextArea > div > div > textarea::placeholder {
    color: #9e8f7a !important;
    opacity: 1 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #4B0082 !important;
    box-shadow: 0 0 0 3px rgba(75,0,130,0.1) !important;
    background: #fffdf7 !important;
}

/* ---- FORGE BUTTON with shimmer ---- */
.stButton > button {
    background: linear-gradient(135deg, #4B0082, #7B2FBE) !important;
    color: #e8c87a !important;
    font-family: 'Cinzel', serif !important;
    font-size: 1.1em !important;
    font-weight: 700 !important;
    letter-spacing: 3px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px 32px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(75,0,130,0.4) !important;
    text-transform: uppercase !important;
    position: relative !important;
    overflow: hidden !important;
    transition: box-shadow 0.3s ease !important;
}

/* Shimmer sweep animation */
.stButton > button::after {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: -100% !important;
    width: 60% !important;
    height: 100% !important;
    background: linear-gradient(
        120deg,
        transparent 0%,
        rgba(255,255,255,0.15) 40%,
        rgba(232,200,122,0.25) 50%,
        rgba(255,255,255,0.15) 60%,
        transparent 100%
    ) !important;
    animation: shimmer 2.8s infinite !important;
}

@keyframes shimmer {
    0%   { left: -100%; }
    60%  { left: 150%; }
    100% { left: 150%; }
}

.stButton > button:hover {
    box-shadow: 0 6px 28px rgba(75,0,130,0.65) !important;
}

/* ---- DOWNLOAD BUTTON ---- */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1a6b3a, #2d9e5a) !important;
    color: #ffffff !important;
    font-family: 'Cinzel', serif !important;
    font-size: 1em !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 28px !important;
    box-shadow: 0 4px 20px rgba(26,107,58,0.4) !important;
}

/* ---- RESULT CARDS ---- */
.result-header {
    background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
    color: #e8c87a;
    font-family: 'Cinzel', serif;
    font-size: 1.4em;
    letter-spacing: 3px;
    padding: 20px 30px;
    border-radius: 12px 12px 0 0;
    text-align: center;
}

.result-body {
    background: #fffdf7;
    background-image: linear-gradient(160deg, #fffef9 0%, #fdf6e3 100%);
    border: 1px solid #e8e0d5;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 28px 32px;
    font-family: 'Lato', sans-serif;
    font-size: 1em;
    line-height: 1.8;
    color: #2c2c2c;
    margin-bottom: 24px;
}

/* Payment button */
.stLinkButton > a {
    background: linear-gradient(135deg, #b8860b, #e8c87a) !important;
    color: #0d0d1a !important;
    font-family: 'Cinzel', serif !important;
    font-size: 1em !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 28px !important;
    box-shadow: 0 4px 20px rgba(184,134,11,0.4) !important;
    text-decoration: none !important;
    display: block !important;
    text-align: center !important;
}

/* Confirmed button */
[data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    border: 1.5px solid #4B0082 !important;
    color: #4B0082 !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 2px !important;
    border-radius: 12px !important;
}            

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# HERO HEADER
# -------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-title">⚡ MYTHOSFORGE AI</div>
    <div class="hero-divider"></div>
    <div class="hero-subtitle">TURN YOUR LIFE INTO AN EPIC PERSONAL MYTHOLOGY</div>
    <div class="hero-tagline">"Every soul carries within it the seeds of legend."</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# FORM CARD
# -------------------------------------------------------
st.markdown('<div class="section-label">✦ Your Identity</div>', unsafe_allow_html=True)
name = st.text_input("", placeholder="Enter your name...", key="name_input",
                     label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Your Essence</div>',
            unsafe_allow_html=True)
bio = st.text_area("", placeholder="Describe yourself — personality, passions, quirks, struggles, what makes you YOU...",
                   height=130, key="bio_input", label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Your Legend Events</div>',
            unsafe_allow_html=True)
events = st.text_area("", placeholder="List 3–5 defining life moments, one per line...\ne.g. Lost my job but built something better\nMoved cities alone at 22\nOvercame crippling self-doubt",
                      height=130, key="events_input", label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Your Sacred Email</div>',
            unsafe_allow_html=True)
email = st.text_input("", placeholder="Where shall we deliver your codex...",
                      key="email_input", label_visibility="collapsed")



# -------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------
def md_to_reportlab(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'^-\s+', '', text.strip())
    return text

def call_llm(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

def generate_pantheon(name, bio, events):
    prompt = f"""
You are a mythologist and storyteller. Based on the person below, create a personal pantheon of 6 gods/deities.
Each god should be inspired by their personality, struggles, hobbies, and life events.

Person's name: {name}
Bio: {bio}
Key life events: {events}

For each god, provide:
- God Name (creative, epic)
- Domain (what they rule over, e.g. "God of Quiet Rebellion")
- Appearance (brief, vivid description)
- Backstory (2-3 sentences connecting to the person's real life)
- Sacred Symbol (one object or image)

Format it clearly with each god separated by a divider line (---).
Make it feel epic, personal, and deeply meaningful.
"""
    return call_llm(prompt)

def generate_legends(name, bio, events):
    prompt = f"""
You are an epic myth writer. Take the real life events below and rewrite each one as a mythic legend.
Make it feel like an ancient story — dramatic, symbolic, and powerful.

Person's name: {name}
Bio: {bio}
Key life events (rewrite EACH one as a legend): {events}

For each event:
- Give it an epic legend title
- Write 3-4 sentences retelling it as mythology

Separate each legend with ---.
"""
    return call_llm(prompt)

def generate_theme_color(name, bio):
    prompt = f"""
Based on this person's personality and life story, pick ONE hex color code that best represents their mythological energy.

Person: {name}
Bio: {bio}

Reply with ONLY a single hex color code like #4B0082. Nothing else.
"""
    color = call_llm(prompt).strip()
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        color = "#4B0082"
    return color

def generate_god_images(pantheon_text):
    images = []
    god_blocks = pantheon_text.split("---")

    for block in god_blocks:
        block = block.strip()
        if not block:
            continue

        god_name = "A deity"
        for line in block.split("\n"):
            clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line.strip())
            if "God Name" in clean:
                parts = clean.split(":", 1)
                if len(parts) > 1:
                    god_name = parts[1].strip()
                    break

        appearance = ""
        for line in block.split("\n"):
            clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line.strip())
            if "Appearance" in clean:
                parts = clean.split(":", 1)
                if len(parts) > 1:
                    appearance = parts[1].strip()
                    break

        if not appearance:
            appearance = f"A divine mythological deity named {god_name}"

        dalle_prompt = (
            f"A dramatic oil painting portrait of a mythological deity. {appearance} "
            f"Style: classical Renaissance oil painting, rich textures, dramatic chiaroscuro "
            f"lighting, painterly brushstrokes, warm candlelit atmosphere, museum quality fine art. "
            f"NO text, NO words, NO letters, NO watermarks, NO signatures anywhere in the image. "
            f"Pure illustration only, no typography of any kind."
        )

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(img_data)
            tmp.close()
            images.append(tmp.name)
        except Exception as e:
            print(f"Image generation failed for {god_name}: {e}")
            images.append(None)

    return images

def build_pdf(name, pantheon_text, legends_text, theme_color="#4B0082", god_images=[]):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("MythTitle", parent=styles["Title"],
                                 fontSize=28, textColor=colors.HexColor(theme_color),
                                 spaceAfter=10, alignment=1)
    subtitle_style = ParagraphStyle("MythSubtitle", parent=styles["Normal"],
                                    fontSize=13, textColor=colors.HexColor(theme_color),
                                    spaceAfter=20, alignment=1)
    section_header_style = ParagraphStyle("SectionHeader", parent=styles["Heading1"],
                                          fontSize=18, textColor=colors.HexColor(theme_color),
                                          spaceBefore=20, spaceAfter=10)
    body_style = ParagraphStyle("MythBody", parent=styles["Normal"],
                                fontSize=11, leading=16, spaceAfter=8,
                                textColor=colors.HexColor("#2C2C2C"))

    story = []
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("⚡ The Mythos Codex", title_style))
    story.append(Paragraph(f"of {name}", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Forged by MythosForge AI", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2,
                            color=colors.HexColor(theme_color)))
    story.append(Spacer(1, 1*cm))

    story.append(Paragraph(f"⚡ The Pantheon of {name}", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor(theme_color)))
    story.append(Spacer(1, 0.3*cm))

    god_blocks = pantheon_text.split("---")
    valid_blocks = [b.strip() for b in god_blocks if b.strip()]

    for i, block in enumerate(valid_blocks):
        if i < len(god_images) and god_images[i]:
            try:
                img = RLImage(god_images[i], width=10*cm, height=10*cm)
                img.hAlign = "CENTER"
                story.append(img)
                story.append(Spacer(1, 0.3*cm))
            except:
                pass
        for line in block.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*cm))
            else:
                story.append(Paragraph(md_to_reportlab(line), body_style))
        story.append(HRFlowable(width="80%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 0.4*cm))

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"📜 The Legends of {name}", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor(theme_color)))
    story.append(Spacer(1, 0.3*cm))

    for line in legends_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
        elif line == "---":
            story.append(HRFlowable(width="80%", thickness=0.5, color=colors.grey))
            story.append(Spacer(1, 0.2*cm))
        else:
            story.append(Paragraph(md_to_reportlab(line), body_style))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor(theme_color)))
    story.append(Paragraph("Generated by MythosForge AI — mythosforge.ai", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

def send_email(recipient_email, name, pdf_buffer):
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    SENDER_PASSWORD = st.secrets["SENDER_PASSWORD"]  # your 16-char app password

    msg = MIMEMultipart()
    msg["From"] = f"MythosForge AI <{SENDER_EMAIL}>"
    msg["To"] = recipient_email
    msg["Subject"] = f"⚡ Your Mythos Codex Awaits, {name}"

    # Email body
    body = f"""
Hail, {name}.

Your personal mythology has been forged in the fires of the cosmos.

Within this sacred codex you will find:
  ✦ Your personal pantheon of gods — born from your very soul
  ✦ Your life events rewritten as epic mythic legends
  ✦ Divine illustrations painted in oils and starlight

Your Mythos Codex is attached to this email as a PDF.

May your legends echo through eternity.

— MythosForge AI
  mythosforge.ai

────────────────────────────────
Note: This codex was uniquely forged for you.
If it arrived in spam, mark it as Not Spam to receive future updates.
"""
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    pdf_buffer.seek(0)
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition",
        f"attachment; filename={name}_Mythos_Codex.pdf"
    )
    msg.attach(attachment)

    # Send
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

# -------------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------------
# Your Lemon Squeezy payment link
PAYMENT_LINK = "https://mythosforge.lemonsqueezy.com/checkout/buy/15fcf7f4-492b-4630-a94f-ceae0162274f"  # paste yours here

generate_btn = st.button("⚡  FORGE MY MYTHOLOGY", use_container_width=True, key="forge_btn")

if generate_btn:
    if not name or not bio or not events or not email:
        st.warning("✦ Please fill in all fields to forge your mythology.")
    else:
        # Save form data to session so it's ready after payment
        st.session_state["pending_name"] = name
        st.session_state["pending_bio"] = bio
        st.session_state["pending_events"] = events
        st.session_state["pending_email"] = email
        st.session_state["show_payment"] = True

# --- Payment Step ---
if st.session_state.get("show_payment") and "pantheon" not in st.session_state:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        margin: 20px 0;
        border: 1px solid #e8c87a33;
    ">
        <div style="font-family: 'Cinzel', serif; color: #e8c87a; font-size: 1.3em; letter-spacing: 2px; margin-bottom: 12px;">
            ✦ ONE LAST STEP
        </div>
        <div style="font-family: 'Lato', sans-serif; color: #a89bc2; font-size: 1em; margin-bottom: 24px; line-height: 1.6;">
            Your mythology awaits. Complete your sacred offering to unlock your personal codex.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button(
            "💳  COMPLETE PAYMENT",
            PAYMENT_LINK,
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    confirmed_btn = st.button(
        "✅  I'VE PAID — GENERATE MY CODEX",
        use_container_width=True,
        key="confirmed_btn"
    )

    if confirmed_btn:
        name = st.session_state["pending_name"]
        bio = st.session_state["pending_bio"]
        events = st.session_state["pending_events"]
        email = st.session_state["pending_email"]

        with st.spinner("⚡ Summoning your pantheon from the cosmos..."):
            pantheon_text = generate_pantheon(name, bio, events)
            legends_text = generate_legends(name, bio, events)
            theme_color = generate_theme_color(name, bio)
            st.session_state["pantheon"] = pantheon_text
            st.session_state["legends"] = legends_text
            st.session_state["name"] = name
            st.session_state["theme_color"] = theme_color

        with st.spinner("🎨 Painting your gods in oils and starlight..."):
            god_images = generate_god_images(pantheon_text)
            pdf_buffer = build_pdf(
                name, pantheon_text, legends_text, theme_color, god_images
            )
            st.session_state["pdf"] = pdf_buffer
            for path in god_images:
                if path and os.path.exists(path):
                    os.remove(path)

        with st.spinner("📜 Delivering your codex across the cosmos..."):
            email_sent = send_email(email, name, pdf_buffer)
            if email_sent:
                st.success(f"✦ Your Mythos Codex has been dispatched to **{email}** — check your inbox!")
            else:
                st.warning("✦ Email delivery failed — but you can still download below!")
# -------------------------------------------------------
# DISPLAY RESULTS
# -------------------------------------------------------
if "pantheon" in st.session_state:
    st.markdown(f'<div class="result-header">⚡ THE PANTHEON OF {st.session_state["name"].upper()}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="result-body">{st.session_state["pantheon"]}</div>',
                unsafe_allow_html=True)

    st.markdown(f'<div class="result-header">📜 THE LEGENDS OF {st.session_state["name"].upper()}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="result-body">{st.session_state["legends"]}</div>',
                unsafe_allow_html=True)

    st.markdown("---")
    st.download_button(
        label="📥  DOWNLOAD YOUR MYTHOS CODEX  —  PDF",
        data=st.session_state["pdf"],
        file_name=f"{st.session_state['name']}_Mythos_Codex.pdf",
        mime="application/pdf",
        use_container_width=True
    )