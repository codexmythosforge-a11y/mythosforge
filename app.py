# -------------------------------------------------------
# MYTHOSFORGE AI — app.py
# -------------------------------------------------------

# --- Standard Library Imports ---
import io
import json
import os
import re
import smtplib
import tempfile
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# --- Third Party Imports ---
import requests
import streamlit as st
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Image as RLImage, Paragraph, SimpleDocTemplate, Spacer
)

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
VERIFIED_EMAILS_FILE = "verified_emails.json"
PAYMENT_LINK_ONETIME = "https://mythforge5.gumroad.com/l/hgbkqy"  # update with new $7 link
PAYMENT_LINK_MONTHLY = "https://mythforge5.gumroad.com/l/bwsvyn"  # update with new $12 link

# --- Clients ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -------------------------------------------------------
# PAYMENT VERIFICATION HELPERS
# -------------------------------------------------------
def load_verified_emails():
    if Path(VERIFIED_EMAILS_FILE).exists():
        with open(VERIFIED_EMAILS_FILE, "r") as f:
            return json.load(f)
    return []

def save_verified_email(email):
    emails = load_verified_emails()
    if email not in emails:
        emails.append(email.lower().strip())
        with open(VERIFIED_EMAILS_FILE, "w") as f:
            json.dump(emails, f)

# Free access emails — for marketing and demo purposes
FREE_ACCESS_EMAILS = [
    "vedextra32@gmail.com",        # yourself
    "friend1@gmail.com",          # marketing friend 1
    "friend2@gmail.com",          # marketing friend 2
    "demo@mythosforge.com",       # demo account
]

def is_email_verified(email):
    clean_email = email.lower().strip()
    # Check free access list first
    if clean_email in [e.lower() for e in FREE_ACCESS_EMAILS]:
        return True
    # Then check paid verified list
    return clean_email in load_verified_emails()

# -------------------------------------------------------
# GUMROAD WEBHOOK HANDLER
# -------------------------------------------------------
params = st.query_params
if "webhook" in params:
    try:
        sale_email = params.get("email", "")
        refunded   = params.get("refunded", "false")
        if sale_email and refunded == "false":
            save_verified_email(sale_email)
    except Exception as e:
        print(f"Webhook error: {e}")

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="MythosForge AI",
    page_icon="⚡",
    layout="centered"
)

# -------------------------------------------------------
# CUSTOM CSS — Fully Responsive
# -------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ---- BASE ---- */
.stApp {
    background-color: #f5f0e8;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23noise)' opacity='0.035'/%3E%3C/svg%3E");
    background-repeat: repeat;
}

/* ---- HERO ---- */
.hero {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 50%, #0d0d1a 100%);
    padding: 60px 24px 50px 24px;
    text-align: center;
    border-radius: 0 0 24px 24px;
    margin: -60px -20px 32px -20px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    position: relative;
    overflow: hidden;
}

.hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background:
        radial-gradient(ellipse at 30% 50%, rgba(123,47,190,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 70% 50%, rgba(232,200,122,0.08) 0%, transparent 50%);
    animation: floatGlow 8s ease-in-out infinite alternate;
    pointer-events: none;
}

.hero::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 50% 100%, rgba(75,0,130,0.2) 0%, transparent 60%);
    animation: pulseGlow 4s ease-in-out infinite alternate;
    pointer-events: none;
}

@keyframes floatGlow {
    0%   { transform: translate(0, 0) scale(1); }
    100% { transform: translate(3%, 5%) scale(1.05); }
}
@keyframes pulseGlow {
    0%   { opacity: 0.5; }
    100% { opacity: 1; }
}

.hero-content { position: relative; z-index: 2; }

.hero-title {
    font-family: 'Cinzel', serif;
    font-size: clamp(1.6em, 5vw, 3em);
    font-weight: 700;
    color: #e8c87a;
    letter-spacing: clamp(2px, 1vw, 4px);
    margin: 0;
    line-height: 1.2;
    text-shadow: 0 0 40px rgba(232,200,122,0.6), 0 0 80px rgba(232,200,122,0.2);
    word-break: keep-all;
    white-space: nowrap;
}

.hero-subtitle {
    font-family: 'Lato', sans-serif;
    font-size: clamp(0.7em, 2.5vw, 1.1em);
    color: #a89bc2;
    margin-top: 10px;
    letter-spacing: clamp(1px, 0.5vw, 2px);
    font-weight: 300;
    padding: 0 10px;
}

.hero-divider {
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #e8c87a, transparent);
    margin: 16px auto;
}

.hero-tagline {
    font-family: 'Cinzel', serif;
    font-size: clamp(0.6em, 1.5vw, 0.78em);
    color: #e8c87a;
    opacity: 0.6;
    letter-spacing: clamp(1px, 0.5vw, 3px);
    margin-top: 14px;
    font-style: italic;
    padding: 0 16px;
}

/* ---- ORNAMENTAL DIVIDER ---- */
.ornament-line {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0;
}
.ornament-line::before,
.ornament-line::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}
.ornament-line span {
    font-family: 'Cinzel', serif;
    color: #c9a84c;
    font-size: 1em;
    white-space: nowrap;
    letter-spacing: 4px;
}

/* ---- HOW IT WORKS ---- */
.how-it-works {
    background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
    border-radius: 16px;
    padding: 32px 20px;
    margin: 24px 0;
    border: 1px solid rgba(232,200,122,0.15);
}
.how-title {
    font-family: 'Cinzel', serif;
    color: #e8c87a;
    font-size: clamp(0.85em, 2vw, 1.2em);
    letter-spacing: 3px;
    text-align: center;
    margin-bottom: 24px;
}
.steps-container {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}
.step {
    flex: 1;
    min-width: 140px;
    text-align: center;
    padding: 18px 12px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    border: 1px solid rgba(232,200,122,0.1);
}
.step-number {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #4B0082, #7B2FBE);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Cinzel', serif;
    color: #e8c87a;
    font-size: 1em;
    font-weight: 700;
    margin: 0 auto 12px auto;
    box-shadow: 0 0 20px rgba(75,0,130,0.4);
}
.step-title {
    font-family: 'Cinzel', serif;
    color: #e8c87a;
    font-size: clamp(0.7em, 1.5vw, 0.85em);
    letter-spacing: 2px;
    margin-bottom: 8px;
}
.step-desc {
    font-family: 'Lato', sans-serif;
    color: #a89bc2;
    font-size: clamp(0.75em, 1.5vw, 0.85em);
    line-height: 1.6;
}

/* ---- PRICING CARDS ---- */
.pricing-container {
    display: flex;
    gap: 16px;
    margin: 16px 0;
    flex-wrap: wrap;
}
.pricing-card {
    flex: 1;
    min-width: 160px;
    border-radius: 16px;
    padding: 24px 16px;
    text-align: center;
    border: 2px solid transparent;
}
.pricing-card.one-time {
    background: linear-gradient(160deg, #fffef9, #fdf6e3);
    border-color: #c9a84c;
}
.pricing-card.monthly {
    background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
    border-color: #4B0082;
    position: relative;
    overflow: hidden;
}
.popular-badge {
    position: absolute;
    top: 10px; right: 10px;
    background: linear-gradient(135deg, #4B0082, #7B2FBE);
    color: #e8c87a;
    font-family: 'Cinzel', serif;
    font-size: 0.6em;
    letter-spacing: 2px;
    padding: 3px 8px;
    border-radius: 20px;
}
.pricing-plan-name {
    font-family: 'Cinzel', serif;
    font-size: clamp(0.7em, 1.5vw, 0.9em);
    letter-spacing: 2px;
    margin-bottom: 10px;
}
.one-time .pricing-plan-name { color: #4B0082; }
.monthly .pricing-plan-name  { color: #a89bc2; }
.pricing-price {
    font-family: 'Cinzel', serif;
    font-size: clamp(1.8em, 4vw, 2.4em);
    font-weight: 700;
    margin-bottom: 4px;
}
.one-time .pricing-price { color: #2c2c2c; }
.monthly .pricing-price  { color: #e8c87a; }
.pricing-period {
    font-family: 'Lato', sans-serif;
    font-size: 0.85em;
    margin-bottom: 14px;
}
.one-time .pricing-period { color: #9e8f7a; }
.monthly .pricing-period  { color: #a89bc2; }
.pricing-feature {
    font-family: 'Lato', sans-serif;
    font-size: clamp(0.75em, 1.5vw, 0.85em);
    margin: 5px 0;
}
.one-time .pricing-feature { color: #5a4a3a; }
.monthly .pricing-feature  { color: #c9b8e8; }

/* ---- FORM ---- */
.section-label {
    font-family: 'Cinzel', serif;
    font-size: 0.85em;
    color: #4B0082;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
    font-weight: 700;
}
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
.stTextInput > div > div > input::placeholder,
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

/* ---- BUTTONS ---- */
.stButton > button {
    background: linear-gradient(135deg, #4B0082, #7B2FBE) !important;
    color: #e8c87a !important;
    font-family: 'Cinzel', serif !important;
    font-size: clamp(0.85em, 2vw, 1.1em) !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 24px !important;
    cursor: pointer !important;
    box-shadow: 0 4px 20px rgba(75,0,130,0.4) !important;
    text-transform: uppercase !important;
    position: relative !important;
    overflow: hidden !important;
    transition: box-shadow 0.3s ease !important;
    width: 100% !important;
}
.stButton > button::after {
    content: '' !important;
    position: absolute !important;
    top: 0 !important; left: -100% !important;
    width: 60% !important; height: 100% !important;
    background: linear-gradient(120deg, transparent 0%,
        rgba(255,255,255,0.15) 40%, rgba(232,200,122,0.25) 50%,
        rgba(255,255,255,0.15) 60%, transparent 100%) !important;
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
.stDownloadButton > button {
    background: linear-gradient(135deg, #1a6b3a, #2d9e5a) !important;
    color: #ffffff !important;
    font-family: 'Cinzel', serif !important;
    font-size: clamp(0.8em, 1.5vw, 1em) !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 20px !important;
    box-shadow: 0 4px 20px rgba(26,107,58,0.4) !important;
}
.stLinkButton > a {
    background: linear-gradient(135deg, #b8860b, #e8c87a) !important;
    color: #0d0d1a !important;
    font-family: 'Cinzel', serif !important;
    font-size: clamp(0.75em, 1.5vw, 1em) !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    box-shadow: 0 4px 20px rgba(184,134,11,0.4) !important;
    text-decoration: none !important;
    display: block !important;
    text-align: center !important;
}

/* ---- RESULT CARDS ---- */
.result-header {
    background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
    color: #e8c87a;
    font-family: 'Cinzel', serif;
    font-size: clamp(0.95em, 2.5vw, 1.4em);
    letter-spacing: 2px;
    padding: 18px 20px;
    border-radius: 12px 12px 0 0;
    text-align: center;
}
.result-body {
    background: #fffdf7;
    background-image: linear-gradient(160deg, #fffef9 0%, #fdf6e3 100%);
    border: 1px solid #e8e0d5;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 24px 20px;
    font-family: 'Lato', sans-serif;
    font-size: clamp(0.9em, 2vw, 1em);
    line-height: 1.8;
    color: #2c2c2c;
    margin-bottom: 20px;
    word-wrap: break-word;
}

/* ---- MOBILE OVERRIDES ---- */
@media (max-width: 640px) {
    .hero { margin: -60px -12px 24px -12px; padding: 50px 16px 40px 16px; }
    .hero-title { font-size: 1.6em; letter-spacing: 2px; }
    .steps-container { flex-direction: column; }
    .step { min-width: unset; }
    .pricing-container { flex-direction: column; }
    .pricing-card { min-width: unset; }
    .result-body { padding: 16px 14px; }
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# HERO HEADER
# -------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="hero-content">
        <div class="hero-title">⚡ MYTHOSFORGE AI</div>
        <div class="hero-divider"></div>
        <div class="hero-subtitle">TURN YOUR LIFE INTO AN EPIC PERSONAL MYTHOLOGY</div>
        <div class="hero-tagline">"Every soul carries within it the seeds of legend."</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ornament-line"><span>✦ ✦ ✦</span></div>', unsafe_allow_html=True)

# ---- HOW IT WORKS ----
st.markdown("""
<div class="how-it-works">
    <div class="how-title">✦ HOW IT WORKS ✦</div>
    <div class="steps-container">
        <div class="step">
            <div class="step-number">I</div>
            <div class="step-title">SHARE YOUR STORY</div>
            <div class="step-desc">Tell us who you are — your passions, struggles, and the moments that shaped you.</div>
        </div>
        <div class="step">
            <div class="step-number">II</div>
            <div class="step-title">THE FORGE AWAKENS</div>
            <div class="step-desc">Our AI mythologist breathes life into your story — crafting gods, legends, and portraits just for you.</div>
        </div>
        <div class="step">
            <div class="step-number">III</div>
            <div class="step-title">RECEIVE YOUR CODEX</div>
            <div class="step-desc">A stunning illustrated PDF Mythos Codex lands straight in your inbox, yours to keep forever.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ornament-line"><span>✦ ✦ ✦</span></div>', unsafe_allow_html=True)

# ---- PRICING ----
st.markdown("""
<div style="font-family: 'Cinzel', serif; color: #4B0082; font-size: clamp(0.8em, 2vw, 1em);
     letter-spacing: 3px; text-align: center; margin-bottom: 16px;">
     ✦ CHOOSE YOUR PATH ✦
</div>
<div class="pricing-container">
    <div class="pricing-card one-time">
        <div class="pricing-plan-name">SINGLE CODEX</div>
        <div class="pricing-price">$7</div>
        <div class="pricing-period">one time</div>
        <div class="pricing-feature">✦ One complete Mythos Codex</div>
        <div class="pricing-feature">✦ AI painted god portraits</div>
        <div class="pricing-feature">✦ Delivered to your inbox</div>
        <div class="pricing-feature">✦ Download forever</div>
    </div>
    <div class="pricing-card monthly">
        <div class="popular-badge">MOST POPULAR</div>
        <div class="pricing-plan-name">ETERNAL FORGE</div>
        <div class="pricing-price">$12</div>
        <div class="pricing-period">per month</div>
        <div class="pricing-feature">✦ Unlimited generations</div>
        <div class="pricing-feature">✦ Update as your life evolves</div>
        <div class="pricing-feature">✦ All future features included</div>
        <div class="pricing-feature">✦ Cancel anytime</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ornament-line"><span>✦ ✦ ✦</span></div>', unsafe_allow_html=True)

# -------------------------------------------------------
# FORM
# -------------------------------------------------------
st.markdown('<div class="section-label">✦ Your Name</div>', unsafe_allow_html=True)
name = st.text_input("", placeholder="What do people call you?", key="name_input",
                     label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Who You Are</div>',
            unsafe_allow_html=True)
bio = st.text_area("", placeholder="Tell us about yourself in your own words — what drives you, what you love, what keeps you up at night, what makes you laugh. The more real you are, the more powerful your mythology will be.",
                   height=130, key="bio_input", label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Your Hobbies & Passions</div>',
            unsafe_allow_html=True)
hobbies = st.text_area("", placeholder="List your hobbies and passions, one per line...\ne.g. Playing chess\nMorning runs\nCooking for friends",
                       height=100, key="hobbies_input", label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Moments That Defined You</div>',
            unsafe_allow_html=True)
events = st.text_area("", placeholder="List 3–5 moments that changed you, one per line...\ne.g. Lost my job but built something better\nMoved cities alone at 22\nOvercame crippling self-doubt",
                      height=130, key="events_input", label_visibility="collapsed")

st.markdown('<div class="section-label" style="margin-top:20px;">✦ Your Email</div>',
            unsafe_allow_html=True)
email = st.text_input("", placeholder="Where should we send your Codex?",
                      key="email_input", label_visibility="collapsed")

# -------------------------------------------------------
# AI HELPER FUNCTIONS
# -------------------------------------------------------
def md_to_reportlab(text):
    """Convert markdown bold to ReportLab tags and strip bullet dashes."""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'^-\s+', '', text.strip())
    return text

def call_llm(prompt):
    """Send a prompt to GPT-4o and return the response text."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    return response.choices[0].message.content

def count_hobbies(hobbies_text):
    """Count the number of hobbies entered — used to decide image count."""
    lines = [l.strip() for l in hobbies_text.strip().split("\n") if l.strip()]
    return max(1, min(len(lines), 6))  # between 1 and 6

def generate_pantheon(name, bio, hobbies, events, num_gods):
    prompt = f"""
You are a gifted mythologist and storyteller with a warm, human voice.
Based on the real person below, create a personal pantheon of exactly {num_gods} gods or goddesses.

Each deity should feel deeply personal — rooted in this person's actual hobbies, struggles, personality quirks, and life experiences. 
Give them names that feel epic but also somehow fitting, as if they were always meant for this person.
Write as if you genuinely know and care about this person's story.

Person's name: {name}
About them: {bio}
Their hobbies and passions: {hobbies}
Key life moments: {events}

For each deity, write:
- God Name (epic, personal, and meaningful)
- Domain (what they govern — make it specific and poetic, e.g. "Goddess of 3am Breakthroughs")
- Appearance (vivid, painterly description — bring them to life)
- Backstory (2-3 warm, personal sentences connecting them to this person's real story)
- Sacred Symbol (one meaningful object or image)

Separate each deity with ---.
Make this feel like something this person will treasure forever.
"""
    return call_llm(prompt)

def generate_legends(name, bio, hobbies, events):
    prompt = f"""
You are a master storyteller with a gift for finding the epic in the everyday.
Take the real life moments below and retell each one as a mythic legend — 
the kind of story that would be whispered around ancient fires.

But keep the human heart of it. Don't make it so grand it feels fake — 
make it feel true AND legendary at the same time. Like this person's life genuinely mattered.

Person's name: {name}
About them: {bio}
Their passions: {hobbies}
Life moments to retell (write a legend for EACH one): {events}

For each moment:
- Give it a legend title that gives you chills
- Write 3-4 sentences retelling it as ancient mythology, 
  keeping the emotional truth of the original moment alive

Separate each legend with ---.
"""
    return call_llm(prompt)

def generate_theme_color(name, bio):
    """Ask GPT to pick a hex color that matches the user's mythological energy."""
    prompt = f"""
You have a poet's eye for color. Based on this person's personality and story,
choose ONE hex color that captures their mythological energy and spirit.

Person: {name}
About them: {bio}

Think carefully — a deep teal for someone restless and searching, 
crimson for fierce passion, gold for ambition, midnight blue for quiet depth.

Reply with ONLY a single hex color code like #4B0082. Nothing else.
"""
    color = call_llm(prompt).strip()
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        color = "#4B0082"
    return color

def generate_god_images(pantheon_text, num_images):
    """Generate one DALL-E oil painting per god, limited to num_images."""
    images = []
    god_blocks = pantheon_text.split("---")
    count = 0

    for block in god_blocks:
        if count >= num_images:
            break
        block = block.strip()
        if not block:
            continue

        # Extract god name
        god_name = "A deity"
        for line in block.split("\n"):
            clean = re.sub(r'\*\*(.*?)\*\*', r'\1', line.strip())
            if "God Name" in clean:
                parts = clean.split(":", 1)
                if len(parts) > 1:
                    god_name = parts[1].strip()
                    break

        # Extract appearance
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
            count += 1
        except Exception as e:
            print(f"Image generation failed for {god_name}: {e}")
            images.append(None)
            count += 1

    return images

# -------------------------------------------------------
# PDF BUILDER
# -------------------------------------------------------
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

    # Cover page
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("⚡ The Mythos Codex", title_style))
    story.append(Paragraph(f"of {name}", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Forged by MythosForge AI", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor(theme_color)))
    story.append(Spacer(1, 1*cm))

    # Pantheon section
    story.append(Paragraph(f"⚡ The Pantheon of {name}", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(theme_color)))
    story.append(Spacer(1, 0.3*cm))

    god_blocks = [b.strip() for b in pantheon_text.split("---") if b.strip()]
    for i, block in enumerate(god_blocks):
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

    # Legends section
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"📜 The Legends of {name}", section_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(theme_color)))
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

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(theme_color)))
    story.append(Paragraph("Generated by MythosForge AI — mythosforge.ai", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -------------------------------------------------------
# EMAIL SENDER
# -------------------------------------------------------
def send_email(recipient_email, name, pdf_buffer):
    SENDER_EMAIL    = st.secrets["SENDER_EMAIL"]
    SENDER_PASSWORD = st.secrets["SENDER_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"]    = f"MythosForge AI <{SENDER_EMAIL}>"
    msg["To"]      = recipient_email
    msg["Subject"] = f"⚡ Your Mythos Codex is here, {name}"

    body = f"""
Hey {name},

Your Mythos Codex has been forged — and honestly, it came out beautifully.

Inside you'll find:
  ✦ Your personal pantheon of gods, born from your own story
  ✦ Your life's defining moments retold as ancient legends
  ✦ Hand-painted portraits of your deities

It's attached to this email as a PDF. Open it somewhere quiet — it deserves that.

May your legends echo through eternity.

— The MythosForge Team
  mythosforge.ai

────────────────────────────────
If this landed in spam, mark it as Not Spam — 
we'd hate for your mythology to get lost in the void.
"""
    msg.attach(MIMEText(body, "plain"))

    pdf_buffer.seek(0)
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition",
                          f"attachment; filename={name}_Mythos_Codex.pdf")
    msg.attach(attachment)

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
generate_btn = st.button("⚡  FORGE MY MYTHOLOGY",
                         use_container_width=True,
                         key="forge_btn")

if generate_btn:
    if not name or not bio or not hobbies or not events or not email:
        st.warning("✦ Please fill in all fields — every detail helps us forge a richer mythology for you.")
    else:
        st.session_state["pending_name"]   = name
        st.session_state["pending_bio"]    = bio
        st.session_state["pending_hobbies"] = hobbies
        st.session_state["pending_events"] = events
        st.session_state["pending_email"]  = email
        st.session_state["show_plan_selection"] = True

# ---- PLAN SELECTION & PAYMENT ----
if st.session_state.get("show_plan_selection") and "pantheon" not in st.session_state:

    st.markdown("""
    <div style="background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
         border-radius: 16px; padding: 32px 24px; margin: 20px 0;
         border: 1px solid rgba(232,200,122,0.2); text-align: center;">
        <div style="font-family: 'Cinzel', serif; color: #e8c87a;
             font-size: clamp(1em, 3vw, 1.2em); letter-spacing: 3px; margin-bottom: 8px;">
            ✦ YOUR STORY IS READY TO BE FORGED
        </div>
        <div style="font-family: 'Lato', sans-serif; color: #a89bc2;
             font-size: clamp(0.85em, 2vw, 0.95em); line-height: 1.6;">
            Choose your path below and we'll bring your mythology to life.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(160deg, #fffef9, #fdf6e3);
             border-radius: 14px; padding: 24px 16px; text-align: center;
             border: 2px solid #c9a84c; margin-bottom: 12px;">
            <div style="font-family: 'Cinzel', serif; color: #4B0082;
                 font-size: 0.8em; letter-spacing: 2px; margin-bottom: 10px;">
                SINGLE CODEX</div>
            <div style="font-family: 'Cinzel', serif; color: #2c2c2c;
                 font-size: 2em; font-weight: 700;">$7</div>
            <div style="font-family: 'Lato', sans-serif; color: #9e8f7a;
                 font-size: 0.85em; margin-bottom: 14px;">one time</div>
            <div style="font-family: 'Lato', sans-serif; color: #5a4a3a;
                 font-size: 0.8em; line-height: 1.8;">
                ✦ One complete Mythos Codex<br>
                ✦ AI painted god portraits<br>
                ✦ Delivered to your inbox<br>
                ✦ Yours forever
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("💳  PAY $7 — ONE TIME", PAYMENT_LINK_ONETIME,
                       use_container_width=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0d0d1a, #1a0a2e);
             border-radius: 14px; padding: 24px 16px; text-align: center;
             border: 2px solid #4B0082; margin-bottom: 12px; position: relative;">
            <div style="position: absolute; top: -11px; left: 50%;
                 transform: translateX(-50%);
                 background: linear-gradient(135deg, #4B0082, #7B2FBE);
                 color: #e8c87a; font-family: 'Cinzel', serif; font-size: 0.6em;
                 letter-spacing: 2px; padding: 3px 14px; border-radius: 20px;
                 white-space: nowrap;">MOST POPULAR</div>
            <div style="font-family: 'Cinzel', serif; color: #a89bc2;
                 font-size: 0.8em; letter-spacing: 2px; margin-bottom: 10px;">
                ETERNAL FORGE</div>
            <div style="font-family: 'Cinzel', serif; color: #e8c87a;
                 font-size: 2em; font-weight: 700;">$12</div>
            <div style="font-family: 'Lato', sans-serif; color: #a89bc2;
                 font-size: 0.85em; margin-bottom: 14px;">per month</div>
            <div style="font-family: 'Lato', sans-serif; color: #c9b8e8;
                 font-size: 0.8em; line-height: 1.8;">
                ✦ Unlimited generations<br>
                ✦ Update as your life evolves<br>
                ✦ All future features included<br>
                ✦ Cancel anytime
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("💳  PAY $12 — PER MONTH", PAYMENT_LINK_MONTHLY,
                       use_container_width=True)

    st.markdown("""
    <div style="text-align:center; font-family: 'Lato', sans-serif;
         color: #9e8f7a; font-size: 0.85em; margin: 20px 0 10px 0;">
        ✦ Already paid? Use the same email address you paid with and click below ✦
    </div>
    """, unsafe_allow_html=True)

    confirmed_btn = st.button("✅  I'VE PAID — GENERATE MY CODEX",
                              use_container_width=True,
                              key="confirmed_btn")

    if confirmed_btn:
        email = st.session_state["pending_email"]

        if not is_email_verified(email):
            st.error("✦ We couldn't verify your payment. Please make sure you used the same email address when paying, then try again.")
        else:
            name   = st.session_state["pending_name"]
            bio    = st.session_state["pending_bio"]
            hobbies = st.session_state["pending_hobbies"]
            events = st.session_state["pending_events"]

            # Smart image count based on hobbies
            num_images = count_hobbies(hobbies)

            with st.spinner("⚡ Summoning your pantheon from the cosmos..."):
                pantheon_text = generate_pantheon(name, bio, hobbies, events, num_images)
                legends_text  = generate_legends(name, bio, hobbies, events)
                theme_color   = generate_theme_color(name, bio)
                st.session_state["pantheon"]    = pantheon_text
                st.session_state["legends"]     = legends_text
                st.session_state["name"]        = name
                st.session_state["theme_color"] = theme_color

            with st.spinner("🎨 Painting your gods in oils and starlight..."):
                god_images = generate_god_images(pantheon_text, num_images)
                pdf_buffer = build_pdf(name, pantheon_text, legends_text,
                                       theme_color, god_images)
                st.session_state["pdf"] = pdf_buffer
                for path in god_images:
                    if path and os.path.exists(path):
                        os.remove(path)

            with st.spinner("📜 Sending your Codex across the cosmos..."):
                email_sent = send_email(email, name, pdf_buffer)
                if email_sent:
                    st.success(f"✦ Your Mythos Codex has been sent to **{email}** — go check your inbox!")
                else:
                    st.warning("✦ Email delivery hit a snag — but you can still download your Codex below!")

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