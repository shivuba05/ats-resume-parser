"""Streamlit Web Application for Resume Analyzer.

High-End Enterprise ATS Recruiter & Resume Intelligence Dashboard:
- Cohesive Dark Theme with Electric Indigo & Emerald Accents
- Google Fonts pairing (Plus Jakarta Sans + Inter + JetBrains Mono)
- Removed Streamlit default chrome & branding while preserving sidebar expand/collapse controls
- Structured layout hierarchy: Hero Header -> Upload Zone -> Empty State / Parsed Results
- Custom-styled Metric Cards (replacing default st.metric)
- Pill-shaped badges for skills, matched competencies, and missing skill gaps
- Full name truncation fix with responsive flex wrapping
- Complete ATS JSON schema export & Styled HTML templates
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List
import streamlit as st
import streamlit.components.v1 as components

from parser.extractor import UnsupportedFormatError, extract_text
from parser.resume_parser import ResumeParser
from parser.template_renderer import render_classic_executive, render_modern_two_column

# Streamlit Page Configuration
st.set_page_config(
    page_title="Resume Intelligence Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


def render_html(html_str: str):
    """Helper to render HTML cleanly in Streamlit without markdown indent interpretation."""
    clean_lines = [line.strip() for line in html_str.strip().split("\n") if line.strip()]
    collapsed_html = "".join(clean_lines)
    st.markdown(collapsed_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# GLOBAL INJECTED STYLESHEET (High-End Dark SaaS Theme)
# ---------------------------------------------------------
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ---------------- Streamlit Header & Navigation ---------------- */
    #MainMenu, footer, [data-testid="stDecoration"] {
        visibility: hidden !important;
        display: none !important;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }

    /* Ensure Streamlit's native sidebar collapse and expand buttons are clearly visible and styled */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] button,
    button[aria-label="Expand sidebar"],
    button[aria-label="Collapse sidebar"],
    button[data-testid="stBaseButton-headerNoPadding"],
    button[kind="header"] {
        visibility: visible !important;
        display: inline-flex !important;
        color: #FFFFFF !important;
        background-color: #111827 !important;
        border: 1px solid #4F46E5 !important;
        border-radius: 8px !important;
    }

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] svg,
    button[aria-label="Expand sidebar"] svg,
    button[aria-label="Collapse sidebar"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* ---------------- Global App Layout & Base Canvas ---------------- */
    html, body, .stApp, [data-testid="stAppViewContainer"], .main, .block-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #090D16 !important;
        color: #F1F5F9 !important;
    }

    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 4rem !important;
        max-width: 1260px !important;
    }

    /* Typography Hierarchy */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        color: #FFFFFF !important;
    }

    /* ---------------- Custom Scrollbar ---------------- */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #090D16;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }

    /* ---------------- Sidebar Styling ---------------- */
    section[data-testid="stSidebar"] {
        background-color: #06080F !important;
        border-right: 1px solid #1E293B !important;
        padding-top: 1.5rem !important;
    }
    section[data-testid="stSidebar"] * {
        color: #94A3B8 !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] strong {
        color: #FFFFFF !important;
    }

    .sidebar-brand-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sidebar-brand-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        font-weight: 800;
        box-shadow: 0 0 14px rgba(99, 102, 241, 0.4);
        flex-shrink: 0;
    }
    .sidebar-brand-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .sidebar-brand-sub {
        font-size: 0.72rem;
        font-weight: 600;
        color: #818CF8 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 2px;
    }

    .sidebar-sec-label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B !important;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-top: 22px;
        margin-bottom: 10px;
    }

    .sidebar-status-box {
        background: #0D1322;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 14px 16px;
        font-size: 0.82rem;
        line-height: 1.7;
        color: #94A3B8 !important;
    }

    /* ---------------- Streamlit Buttons ---------------- */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        border: 1px solid #6366F1 !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%) !important;
        border-color: #818CF8 !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
        transform: translateY(-1px) !important;
        color: #FFFFFF !important;
    }

    /* ---------------- Streamlit Radio Buttons (Electric Indigo Accent - No Red) ---------------- */
    div[data-testid="stRadio"] > div {
        background: #0E1526 !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        padding: 8px 14px !important;
        gap: 12px !important;
    }
    div[data-testid="stRadio"] label {
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #CBD5E1 !important;
        cursor: pointer !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {
        background-color: #6366F1 !important;
        border-color: #6366F1 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] > div {
        background-color: #FFFFFF !important;
    }
    div[data-testid="stRadio"] input[type="radio"]:checked + div {
        background-color: #6366F1 !important;
        border-color: #6366F1 !important;
    }
    div[data-testid="stRadio"] input[type="radio"]:checked + div > div {
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="radio"] div[aria-checked="true"] {
        background-color: #6366F1 !important;
        border-color: #6366F1 !important;
    }
    div[data-baseweb="radio"] div[aria-checked="true"] > div {
        background-color: #FFFFFF !important;
    }

    /* ---------------- Streamlit File Uploader ---------------- */
    div[data-testid="stFileUploader"] {
        background: #0E1526 !important;
        border: 1.5px dashed #2B3B55 !important;
        border-radius: 14px !important;
        padding: 16px 22px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #6366F1 !important;
        background: #111A30 !important;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.15) !important;
    }
    div[data-testid="stFileUploader"] section {
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #6366F1 !important;
        border-radius: 8px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3) !important;
    }
    div[data-testid="stFileUploader"] button:hover {
        background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%) !important;
        border-color: #818CF8 !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="textarea"] textarea, div[data-baseweb="input"] input {
        background-color: #0E1526 !important;
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-baseweb="textarea"] textarea:focus, div[data-baseweb="input"] input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #0E1526 !important;
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        color: #F8FAFC !important;
    }

    /* Slider styling */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #6366F1 !important;
        border-color: #818CF8 !important;
        box-shadow: 0 0 12px rgba(99, 102, 241, 0.6) !important;
    }
    div[data-baseweb="slider"] div[data-testid="stSliderTickBar"] {
        background-color: #1E293B !important;
    }
    div[data-baseweb="slider"] div[data-testid="stSliderTrackFilled"] {
        background-color: #6366F1 !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #4F46E5 0%, #6366F1 60%, #38BDF8 100%) !important;
        border-radius: 6px !important;
    }
    .stProgress > div > div > div {
        background-color: #1E293B !important;
        border-radius: 6px !important;
    }

    /* Streamlit Tabs */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #94A3B8 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.94rem !important;
        padding: 12px 20px !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 8px 8px 0 0 !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #F8FAFC !important;
        background-color: rgba(99, 102, 241, 0.08) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #111827 !important;
        color: #818CF8 !important;
        border-bottom: 2px solid #6366F1 !important;
        font-weight: 700 !important;
    }

    /* Code block */
    [data-testid="stCodeBlock"] {
        background-color: #0B0F19 !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
    }
    [data-testid="stCodeBlock"] code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.86rem !important;
        color: #E2E8F0 !important;
    }

    /* ---------------- High-Impact Product Hero Header ---------------- */
    .product-hero-header {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }
    .product-hero-header::before {
        content: "";
        position: absolute;
        top: -60px;
        right: -60px;
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, rgba(99, 102, 241, 0) 70%);
        pointer-events: none;
    }
    .hero-badge-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.4);
        color: #A5B4FC;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 9999px;
    }
    .hero-version-tag {
        font-size: 0.76rem;
        font-weight: 600;
        color: #64748B;
    }
    .product-main-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin: 0 0 8px 0;
        letter-spacing: -0.03em;
    }
    .product-subtitle {
        font-size: 0.96rem;
        color: #94A3B8 !important;
        margin: 0;
        line-height: 1.6;
        max-width: 850px;
    }

    /* ---------------- Ingestion Zone Card ---------------- */
    .ingestion-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .ingestion-card-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .ingestion-card-sub {
        font-size: 0.88rem;
        color: #94A3B8 !important;
        margin-bottom: 18px;
    }

    /* ---------------- Empty State Placeholder ---------------- */
    .empty-state-card {
        background: #111827;
        border: 1.5px dashed #2B3B55;
        border-radius: 16px;
        padding: 50px 30px;
        text-align: center;
        margin-top: 28px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .empty-state-icon {
        font-size: 3.2rem;
        margin-bottom: 14px;
    }
    .empty-state-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 8px;
    }
    .empty-state-desc {
        font-size: 0.94rem;
        color: #94A3B8 !important;
        max-width: 540px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* ---------------- ATS Match Score Banner ---------------- */
    .match-score-hero-box {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.45) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 16px;
        padding: 22px 28px;
        box-shadow: 0 0 24px rgba(16, 185, 129, 0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 20px;
    }
    .match-score-pill-tag {
        font-size: 0.72rem;
        font-weight: 800;
        color: #34D399;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .match-score-info-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.45rem;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
    }
    .match-score-info-sub {
        font-size: 0.92rem;
        color: #A7F3D0 !important;
        margin-top: 6px;
        line-height: 1.5;
    }
    .match-score-circle {
        width: 82px;
        height: 82px;
        border-radius: 50%;
        background: #022C22;
        border: 2.5px solid #34D399;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 16px rgba(52, 211, 153, 0.35);
        flex-shrink: 0;
    }
    .match-score-number {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.75rem;
        font-weight: 800;
        color: #34D399 !important;
        line-height: 1;
    }
    .match-score-label {
        font-size: 0.58rem;
        font-weight: 800;
        color: #A7F3D0 !important;
        letter-spacing: 0.6px;
        margin-top: 2px;
    }

    /* ---------------- Candidate Profile Hero Card ---------------- */
    .hero-profile-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 26px 30px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        display: flex;
        align-items: flex-start;
        gap: 24px;
        position: relative;
    }
    .hero-avatar {
        width: 80px;
        height: 80px;
        border-radius: 18px;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 2px solid #6366F1;
        color: #A5B4FC;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.85rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 0 16px rgba(99, 102, 241, 0.25);
    }
    .hero-details {
        flex-grow: 1;
        min-width: 0;
    }
    .hero-name-row {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 8px;
    }
    .hero-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: clamp(1.4rem, 2.2vw, 1.85rem);
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.025em;
        word-break: break-word;
        overflow-wrap: break-word;
        white-space: normal;
        margin: 0;
        line-height: 1.25;
    }
    .hero-role-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }
    .hero-role-badge {
        background: rgba(99, 102, 241, 0.15);
        color: #C7D2FE !important;
        font-size: 0.86rem;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 9999px;
        border: 1px solid rgba(99, 102, 241, 0.35);
    }
    .hero-summary {
        font-size: 0.94rem;
        color: #CBD5E1 !important;
        line-height: 1.65;
        margin-top: 10px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .hero-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .action-icon-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border: 1px solid #2B3B55;
        border-radius: 8px;
        color: #CBD5E1 !important;
        text-decoration: none;
        background: #1E293B;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .action-icon-btn:hover {
        background: #2B3B55;
        border-color: #6366F1;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }

    /* ---------------- 4 Stat Metrics Row ---------------- */
    .stat-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .stat-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.3);
    }
    .stat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }
    .stat-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        color: #94A3B8 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .stat-icon-circle {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
    }
    .stat-value-row {
        display: flex;
        align-items: baseline;
        gap: 10px;
    }
    .stat-number {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.15rem;
        font-weight: 800;
        color: #FFFFFF !important;
        line-height: 1;
    }
    .stat-sub {
        font-size: 0.84rem;
        font-weight: 600;
        color: #94A3B8 !important;
    }

    /* ---------------- Unified Clean Cards ---------------- */
    .clean-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .clean-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 6px;
        flex-wrap: wrap;
        gap: 8px;
    }
    .clean-card-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF !important;
    }
    .clean-card-subtitle {
        font-size: 0.95rem;
        font-weight: 600;
        color: #818CF8 !important;
        margin-bottom: 12px;
    }
    .clean-date-chip {
        background: #1E293B;
        color: #94A3B8 !important;
        border: 1px solid #2A374A;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.3px;
    }
    .clean-bullet-item {
        font-size: 0.92rem;
        color: #CBD5E1 !important;
        line-height: 1.65;
        margin-bottom: 8px;
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }
    .clean-bullet-dot {
        color: #6366F1 !important;
        font-size: 0.75rem;
        margin-top: 4px;
    }
    .clean-tags-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid #1E293B;
    }
    .clean-tag {
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #C7D2FE !important;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
    }

    /* ---------------- Pill-Shaped Badges ---------------- */
    .skills-matrix-card {
        background: #111827;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 24px 26px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .matrix-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid #1E293B;
    }
    .matrix-category-label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        color: #94A3B8 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 18px;
        margin-bottom: 10px;
    }
    .matrix-category-label:first-of-type {
        margin-top: 0;
    }
    .matrix-tags-group {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 14px;
    }
    .skill-badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.35);
        color: #C7D2FE !important;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.84rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .skill-badge-pill:hover {
        background: rgba(99, 102, 241, 0.22);
        border-color: #818CF8;
        transform: translateY(-1px);
    }
    .skill-badge-pill.success {
        background: rgba(16, 185, 129, 0.15) !important;
        border-color: rgba(52, 211, 153, 0.45) !important;
        color: #6EE7B7 !important;
        font-weight: 600;
    }
    .skill-badge-pill.danger {
        background: rgba(239, 68, 68, 0.15) !important;
        border-color: rgba(248, 113, 113, 0.45) !important;
        color: #FCA5A5 !important;
        font-weight: 600;
    }
    .skill-badge-pill.lang {
        background: rgba(6, 78, 59, 0.35) !important;
        border-color: rgba(16, 185, 129, 0.4) !important;
        color: #34D399 !important;
        font-weight: 600;
    }
    .skill-badge-pill.interest {
        background: rgba(180, 83, 9, 0.25) !important;
        border-color: rgba(245, 158, 11, 0.4) !important;
        color: #FCD34D !important;
        font-weight: 600;
    }

    /* Section Title inside Tabs */
    .tab-section-header {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""")


def get_parser(threshold: float) -> ResumeParser:
    """Instantiate ResumeParser with the selected fuzzy threshold."""
    return ResumeParser(skill_fuzzy_threshold=threshold)


def get_initials(name: str) -> str:
    """Generate 2-letter uppercase initials from candidate name."""
    if not name or name in ("Candidate Profile", "Not Specified", "Candidate Name"):
        return "CV"
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    return "CV"


def compute_match_score(skills: List[str], exp_count: int, edu_count: int, threshold: float) -> tuple[int, str]:
    """Compute ATS match score based on overall profile completeness."""
    base = min(len(skills) * 5, 50) + min(exp_count * 15, 30) + min(edu_count * 10, 20)
    adjusted = int(base * (threshold / 85.0))
    score = max(65, min(adjusted, 98))
    desc = f"🔥 Profile Completeness: {len(skills)} technical & domain skills verified, {exp_count} career milestones, {edu_count} education records."
    return score, desc


def main():
    # ---------------------------------------------------------
    # SIDEBAR: Engine Configuration & Ontology Pipeline
    # ---------------------------------------------------------
    with st.sidebar:
        render_html("""
        <div class="sidebar-brand-card">
            <div class="sidebar-brand-icon">⚡</div>
            <div>
                <div class="sidebar-brand-title">Resume Analyzer</div>
                <div class="sidebar-brand-sub">ATS Intelligence Studio</div>
            </div>
        </div>
        <div class="sidebar-sec-label">ENGINE SETTINGS</div>
        """)

        # Matching Sensitivity Slider
        fuzzy_threshold = st.slider(
            "Fuzzy Match Sensitivity:",
            min_value=60,
            max_value=100,
            value=85,
            step=1,
            help="Higher values (90-100) enforce exact matching. Balanced values (80-89) catch standard aliases like React vs React.js. Lower values (<80) catch broad abbreviations."
        )

        if fuzzy_threshold >= 90:
            st.info("🎯 **Strict Mode** (Exact token match)")
        elif fuzzy_threshold >= 80:
            st.success("⚖️ **Balanced Mode** (Recommended)")
        else:
            st.warning("🌐 **Broad Mode** (Partial abbreviations)")

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        render_html("""
        <div class="sidebar-sec-label">PIPELINE ARCHITECTURE</div>
        <div class="sidebar-status-box">
            • <strong>NLP Pipeline:</strong> Active (spaCy)<br>
            • <strong>EntityRuler:</strong> Custom Canonical<br>
            • <strong>Degree Normalizer:</strong> Active<br>
            • <strong>Skills Ontology:</strong> 75+ Domain Nodes<br>
            • <strong>PDF Parser:</strong> pypdf + pdfminer<br>
            • <strong>DOCX Engine:</strong> python-docx + XML
        </div>
        """)

    # ---------------------------------------------------------
    # 1. PRODUCT HERO HEADER & ENGINE CONTROLS
    # ---------------------------------------------------------
    render_html("""
    <div class="product-hero-header">
        <div class="hero-badge-row">
            <span class="hero-badge">⚡ NEXT-GEN ATS INTELLIGENCE</span>
            <span class="hero-version-tag">Enterprise Edition • v2.4</span>
        </div>
        <h1 class="product-main-title">Resume Intelligence & ATS Studio</h1>
        <p class="product-subtitle">Autonomous document ingestion, semantic skill graph extraction, and precision role alignment dashboard.</p>
    </div>
    """)

    # In-page Settings Expander (Direct access regardless of sidebar state)
    with st.expander("⚡ ATS Engine Configuration & Matching Sensitivity", expanded=False):
        c_set1, c_set2 = st.columns([1.4, 1])
        with c_set1:
            inpage_threshold = st.slider(
                "Fuzzy Match Sensitivity Threshold:",
                min_value=60,
                max_value=100,
                value=int(fuzzy_threshold),
                step=1,
                key="inpage_thresh",
                help="Higher values (90-100) enforce strict token matching. Balanced values (80-89) catch standard aliases. Lower values (<80) catch broad abbreviations."
            )
            fuzzy_threshold = inpage_threshold
            if fuzzy_threshold >= 90:
                st.info("🎯 **Strict Mode** (Exact token match)")
            elif fuzzy_threshold >= 80:
                st.success("⚖️ **Balanced Mode** (Recommended)")
            else:
                st.warning("🌐 **Broad Mode** (Partial abbreviations)")
        with c_set2:
            render_html("""
            <div class="sidebar-status-box" style="margin-top: 6px;">
                • <strong>NLP Pipeline:</strong> spaCy + EntityRuler<br>
                • <strong>Degree Normalizer:</strong> Standardized Schema<br>
                • <strong>Skills Ontology:</strong> 75+ Domain Nodes<br>
                • <strong>Extraction Engines:</strong> PDF + DOCX (XML-native)
            </div>
            """)

    # ---------------------------------------------------------
    # 2. RESUME INGESTION & UPLOAD ZONE (Default: Empty State)
    # ---------------------------------------------------------
    render_html("""
    <div class="ingestion-card">
        <div class="ingestion-card-title">📁 Ingestion & Document Source</div>
        <div class="ingestion-card-sub">Choose an ingestion method below. Upload a candidate document, select a benchmark resume, or paste raw text.</div>
    </div>
    """)

    sample_dir = Path("tests/sample_resumes")
    sample_files = []
    if sample_dir.exists():
        sample_files = sorted([f.name for f in sample_dir.glob("*.*") if f.suffix.lower() in [".pdf", ".docx"]])

    input_mode = st.radio(
        "Choose Ingestion Method:",
        options=["📁 Upload File (PDF / DOCX)", "📂 Load Pre-Built Sample", "📝 Direct Text Stream"],
        horizontal=True,
        label_visibility="collapsed"
    )

    file_to_parse = None
    file_name = ""
    direct_pasted_text = ""

    col_input, _ = st.columns([1, 0.01])
    with col_input:
        if "Upload" in input_mode:
            uploaded_file = st.file_uploader(
                "Upload Candidate Document (PDF or DOCX)",
                type=["pdf", "docx"],
                help="Supported file formats: PDF documents and Microsoft Word DOCX files"
            )
            if uploaded_file is not None:
                file_to_parse = uploaded_file
                file_name = uploaded_file.name

        elif "Sample" in input_mode:
            sample_choice = st.selectbox(
                "Select a pre-built benchmark resume:",
                options=["-- Select a sample resume --"] + sample_files,
                index=0
            )
            if sample_choice and not sample_choice.startswith("--"):
                file_to_parse = sample_dir / sample_choice
                file_name = sample_choice

        else:
            direct_pasted_text = st.text_area(
                "Paste raw resume text below:",
                value="",
                placeholder="Paste candidate resume text here to analyze...",
                height=180
            )
            if direct_pasted_text.strip():
                file_name = "Pasted_Resume_Text.txt"

    # Empty State Check: If no resume is uploaded/selected/pasted, show clean waiting state
    if not file_to_parse and not direct_pasted_text.strip():
        render_html("""
        <div class="empty-state-card">
            <div class="empty-state-icon">📄</div>
            <div class="empty-state-title">No Candidate Resume Loaded</div>
            <div class="empty-state-desc">Upload a PDF or DOCX file, select a pre-built benchmark profile, or paste raw text above to initiate parsing and generate ATS insights.</div>
        </div>
        """)
        return

    # Execute Parser Pipeline
    parser = get_parser(float(fuzzy_threshold))
    parsed_data: Dict[str, Any] = {}
    raw_text = ""

    try:
        if direct_pasted_text.strip():
            raw_text = direct_pasted_text
            parsed_data = parser.parse_text(raw_text, threshold=float(fuzzy_threshold))
        elif file_to_parse is not None:
            if isinstance(file_to_parse, Path):
                raw_text = extract_text(str(file_to_parse))
                parsed_data = parser.parse_text(raw_text, threshold=float(fuzzy_threshold))
            else:
                bytes_data = file_to_parse.getvalue()
                raw_text = extract_text(bytes_data, file_name=file_name)
                parsed_data = parser.parse_text(raw_text, threshold=float(fuzzy_threshold))
    except Exception as e:
        st.error(f"Error parsing resume: {e}")
        parsed_data = {}

    contact = parsed_data.get("contact", {})
    name = contact.get("name") or "Candidate Profile"
    email = contact.get("email") or ""
    phone = contact.get("phone") or ""
    linkedin = contact.get("linkedin") or ""
    portfolio = contact.get("portfolio") or ""

    summary = parsed_data.get("summary") or ""
    skills = parsed_data.get("skills", [])
    experience = parsed_data.get("experience", [])
    education = parsed_data.get("education", [])
    projects = parsed_data.get("projects", [])
    languages = parsed_data.get("languages", [])
    hobbies = parsed_data.get("hobbies", [])
    certifications = parsed_data.get("certifications", [])

    categorized_skills = parser.skill_matcher.get_categorized_skills(skills)
    match_score, match_desc = compute_match_score(skills, len(experience), len(education), float(fuzzy_threshold))

    top_title = "Senior Professional"
    if experience and experience[0].get("title"):
        top_title = experience[0].get("title")

    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 3. ANCHORED ATS MATCH SCORE BANNER
    # ---------------------------------------------------------
    render_html(f"""
    <div class="match-score-hero-box">
        <div>
            <div class="match-score-pill-tag">⚡ ATS BENCHMARK SCORE</div>
            <div class="match-score-info-title">ATS Match Fit: {match_score}%</div>
            <div class="match-score-info-sub">{match_desc}</div>
        </div>
        <div class="match-score-circle">
            <div class="match-score-number">{match_score}%</div>
            <div class="match-score-label">MATCH FIT</div>
        </div>
    </div>
    """)

    # ---------------------------------------------------------
    # 4. HERO CANDIDATE PROFILE CARD (With Truncation Fix)
    # ---------------------------------------------------------
    initials = get_initials(name)
    mailto_link = f'href="mailto:{email}"' if email else ''
    tel_link = f'href="tel:{phone}"' if phone else ''
    profile_link = f'href="{linkedin or portfolio or "#"}" target="_blank"'

    summary_html = f'<div class="hero-summary">{summary}</div>' if summary else '<div class="hero-summary" style="color:#64748B; font-style:italic;">No profile summary provided in parsed document.</div>'

    contact_badges = []
    if email:
        contact_badges.append(f'<a class="action-icon-btn" {mailto_link} title="Email Candidate">✉️ {email}</a>')
    if phone:
        contact_badges.append(f'<a class="action-icon-btn" {tel_link} title="Call Candidate">📞 {phone}</a>')
    if linkedin or portfolio:
        contact_badges.append(f'<a class="action-icon-btn" {profile_link} title="LinkedIn / Portfolio">🔗 Portfolio</a>')

    actions_html = "".join(contact_badges)

    render_html(f"""
    <div class="hero-profile-card">
        <div class="hero-avatar">{initials}</div>
        <div class="hero-details">
            <div class="hero-name-row">
                <h2 class="hero-name">{name}</h2>
                <div class="hero-actions">
                    {actions_html}
                </div>
            </div>
            <div class="hero-role-row">
                <span class="hero-role-badge">{top_title}</span>
            </div>
            {summary_html}
        </div>
    </div>
    """)

    # ---------------------------------------------------------
    # 5. 4-STAT METRICS ROW (Custom Styled Cards)
    # ---------------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_html(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-title">SKILLS MATCHED</span>
                <div class="stat-icon-circle" style="background:rgba(16, 185, 129, 0.15); color:#34D399;">⚡</div>
            </div>
            <div class="stat-value-row">
                <span class="stat-number">{len(skills)}</span>
                <span class="stat-sub" style="color:#34D399;">Verified</span>
            </div>
        </div>
        """)
    with m2:
        render_html(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-title">EXPERIENCE</span>
                <div class="stat-icon-circle" style="background:rgba(99, 102, 241, 0.15); color:#818CF8;">💼</div>
            </div>
            <div class="stat-value-row">
                <span class="stat-number">{len(experience)}</span>
                <span class="stat-sub">Milestones</span>
            </div>
        </div>
        """)
    with m3:
        render_html(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-title">EDUCATION</span>
                <div class="stat-icon-circle" style="background:rgba(56, 189, 248, 0.15); color:#38BDF8;">🎓</div>
            </div>
            <div class="stat-value-row">
                <span class="stat-number">{len(education)}</span>
                <span class="stat-sub">Credentials</span>
            </div>
        </div>
        """)
    with m4:
        render_html(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-title">PROJECTS</span>
                <div class="stat-icon-circle" style="background:rgba(245, 158, 11, 0.15); color:#FBBF24;">🚀</div>
            </div>
            <div class="stat-value-row">
                <span class="stat-number">{len(projects)}</span>
                <span class="stat-sub">Showcases</span>
            </div>
        </div>
        """)

    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 6. UNIFIED DASHBOARD TABS
    # ---------------------------------------------------------
    tab_overview, tab_matcher, tab_templates, tab_analytics, tab_json, tab_raw = st.tabs([
        "📊 Overview & Timeline",
        "🎯 Target Job Matcher",
        "📄 Styled Resume Preview",
        "📈 Skill Analytics",
        "🔍 ATS JSON Inspector",
        "📄 Raw Document Text"
    ])

    # Tab 1: Overview & Timeline
    with tab_overview:
        col_timeline, col_matrix = st.columns([1.85, 1.15])

        with col_timeline:
            render_html('<div class="tab-section-header">💼 Career Milestones & Experience</div>')
            
            if experience:
                for exp in experience:
                    title = exp.get("title") or "Position"
                    company = exp.get("company") or "Company"
                    dates = exp.get("dates") or "Present"
                    desc = exp.get("description") or ""

                    bullets_list = []
                    for line in desc.split("\n"):
                        clean_l = line.strip(" -•*")
                        if clean_l:
                            bullets_list.append(f'<div class="clean-bullet-item"><span class="clean-bullet-dot">●</span><span>{clean_l}</span></div>')
                    bullets_html = "".join(bullets_list)

                    matched_job_tags = [s for s in skills if s.lower() in desc.lower() or s.lower() in title.lower()]
                    job_tags_html = ""
                    if matched_job_tags:
                        tag_chips = "".join([f'<span class="clean-tag">{t}</span>' for t in matched_job_tags[:5]])
                        job_tags_html = f'<div class="clean-tags-row">{tag_chips}</div>'

                    render_html(f"""
                    <div class="clean-card">
                        <div class="clean-card-header">
                            <div class="clean-card-title">{title}</div>
                            <span class="clean-date-chip">{dates}</span>
                        </div>
                        <div class="clean-card-subtitle">{company}</div>
                        <div style="margin-top: 8px;">{bullets_html}</div>
                        {job_tags_html}
                    </div>
                    """)
            else:
                st.info("No work experience records parsed from this document.")

            render_html('<div class="tab-section-header" style="margin-top: 24px;">🎓 Education & Degrees</div>')
            if education:
                for edu in education:
                    deg = edu.get("degree") or "Degree"
                    inst = edu.get("institution") or "University"
                    dates = edu.get("dates") or ""

                    render_html(f"""
                    <div class="clean-card">
                        <div class="clean-card-header">
                            <div class="clean-card-title">{deg}</div>
                            {f'<span class="clean-date-chip">{dates}</span>' if dates else ''}
                        </div>
                        <div class="clean-card-subtitle">{inst}</div>
                    </div>
                    """)
            else:
                st.info("No formal education records parsed.")

            if projects:
                render_html('<div class="tab-section-header" style="margin-top: 24px;">🚀 Notable Projects & Works</div>')
                for proj in projects:
                    p_name = proj.get("name") or "Project"
                    p_desc = proj.get("description") or ""
                    render_html(f"""
                    <div class="clean-card">
                        <div class="clean-card-title">{p_name}</div>
                        <div style="font-size:0.92rem; color:#CBD5E1; margin-top:8px; line-height:1.6;">{p_desc}</div>
                    </div>
                    """)

        with col_matrix:
            matrix_sections_list = []
            if categorized_skills:
                for cat_name, cat_skills in categorized_skills.items():
                    cat_pills = "".join([f'<span class="skill-badge-pill">{s}</span>' for s in cat_skills])
                    matrix_sections_list.append(f'<div class="matrix-category-label">{cat_name}</div><div class="matrix-tags-group">{cat_pills}</div>')
            else:
                all_pills = "".join([f'<span class="skill-badge-pill">{s}</span>' for s in skills])
                matrix_sections_list.append(f'<div class="matrix-tags-group">{all_pills}</div>')

            matrix_rendered = "".join(matrix_sections_list)

            render_html(f"""
            <div class="skills-matrix-card">
                <div class="matrix-title">⚡ Skills Matrix</div>
                {matrix_rendered}
            </div>
            """)

            if languages or hobbies:
                lang_pills = "".join([f'<span class="skill-badge-pill lang">🗣️ {l}</span>' for l in languages])
                hobby_pills = "".join([f'<span class="skill-badge-pill interest">⭐ {h}</span>' for h in hobbies])

                lang_sec = f'<div class="matrix-category-label">KNOWN LANGUAGES</div><div class="matrix-tags-group">{lang_pills}</div>' if languages else ''
                hobby_sec = f'<div class="matrix-category-label">HOBBIES & INTERESTS</div><div class="matrix-tags-group">{hobby_pills}</div>' if hobbies else ''

                render_html(f"""
                <div class="skills-matrix-card" style="margin-top: 20px;">
                    <div class="matrix-title">🌐 Languages & Interests</div>
                    {lang_sec}
                    {hobby_sec}
                </div>
                """)

    # Tab 2: Job Matcher
    with tab_matcher:
        render_html('<div class="tab-section-header">🎯 Target Job Description Matcher & Gap Analysis</div>')
        st.write("Paste target job posting requirements below to calculate exact qualification alignment and missing skill gaps.")

        jd_text = st.text_area(
            "Target Job Requirements:",
            value="We are looking for a Senior Engineer with strong proficiency in Python, TypeScript, React, Docker, Kubernetes, and AWS microservices. Experience with Apache Kafka and PostgreSQL is a strong plus.",
            height=130
        )

        if jd_text:
            jd_skills = parser.skill_matcher.extract_skills(jd_text, threshold=float(fuzzy_threshold))
            candidate_skill_set = set(s.lower() for s in skills)
            
            matched_skills = [s for s in jd_skills if s.lower() in candidate_skill_set]
            missing_skills = [s for s in jd_skills if s.lower() not in candidate_skill_set]
            
            jd_score = int((len(matched_skills) / max(len(jd_skills), 1)) * 100)

            render_html(f"""
            <div class="match-score-hero-box" style="margin-top: 20px;">
                <div>
                    <div class="match-score-pill-tag">🎯 ROLE ALIGNMENT SCORE</div>
                    <div class="match-score-info-title">Target Job Match: {jd_score}%</div>
                    <div class="match-score-info-sub">Matched <strong>{len(matched_skills)}</strong> of <strong>{len(jd_skills)}</strong> required competencies for this job description.</div>
                </div>
                <div class="match-score-circle">
                    <div class="match-score-number">{jd_score}%</div>
                    <div class="match-score-label">JD FIT</div>
                </div>
            </div>
            """)

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                render_html(f'<div class="tab-section-header" style="font-size:1.05rem; color:#34D399 !important;">✓ Matched Skills ({len(matched_skills)})</div>')
                pills = "".join([f'<span class="skill-badge-pill success">✓ {s}</span>' for s in matched_skills])
                render_html(f'<div class="matrix-tags-group">{pills}</div>' if pills else '<p style="color:#94A3B8;">No exact skill overlap detected.</p>')

            with col_m2:
                render_html(f'<div class="tab-section-header" style="font-size:1.05rem; color:#F87171 !important;">✕ Missing Skill Gaps ({len(missing_skills)})</div>')
                pills = "".join([f'<span class="skill-badge-pill danger">✕ {s}</span>' for s in missing_skills])
                render_html(f'<div class="matrix-tags-group">{pills}</div>' if pills else '<p style="color:#34D399; font-weight:600;">✨ Zero missing skills! Perfect 100% competency match.</p>')

    # Tab 3: Styled Resume Templates
    with tab_templates:
        render_html('<div class="tab-section-header">📄 Visual Resume Template Export</div>')
        
        template_choice = st.radio(
            "Select Resume Template Style:",
            options=["Modern Two-Column Layout", "Classic Executive Layout"],
            horizontal=True,
            key=f"tpl_choice_{Path(file_name).stem}"
        )

        if "Modern" in template_choice:
            styled_html = render_modern_two_column(parsed_data)
        else:
            styled_html = render_classic_executive(parsed_data)

        components.html(styled_html, height=850, scrolling=True)

        clean_stem = Path(file_name).stem if file_name else "candidate_resume"
        html_hash = hashlib.md5(f"{file_name}_{styled_html}".encode("utf-8")).hexdigest()

        st.download_button(
            label=f"📄 Download Styled HTML Resume ({clean_stem}.html)",
            data=styled_html,
            file_name=f"{clean_stem}_styled_resume.html",
            mime="text/html",
            key=f"dl_styled_html_{html_hash}"
        )

    # Tab 4: Skill Analytics
    with tab_analytics:
        render_html('<div class="tab-section-header">📈 Skill Category Distribution & Density</div>')
        if categorized_skills:
            for cat, c_skills in categorized_skills.items():
                st.markdown(f"**{cat}** — `{len(c_skills)} skills` ({', '.join(c_skills)})")
                progress_val = min(len(c_skills) / 8.0, 1.0)
                st.progress(progress_val)
        else:
            st.info("No skill categories found in this document.")

    # Tab 5: ATS JSON Inspector
    with tab_json:
        clean_stem = Path(file_name).stem if file_name else "candidate_resume"
        render_html(f"""
        <div class="tab-section-header">
            🔍 Standard ATS JSON Schema Output — <span style="font-size:0.9rem; font-weight:500; color:#818CF8;">Active Profile: {name} ({file_name})</span>
        </div>
        """)
        json_str = json.dumps(parsed_data, indent=2, ensure_ascii=False)
        st.code(json_str, language="json")

        json_hash = hashlib.md5(f"{file_name}_{json_str}".encode("utf-8")).hexdigest()

        st.download_button(
            label=f"📥 Download ATS JSON Export ({clean_stem}.json)",
            data=json_str,
            file_name=f"{clean_stem}_ats_parsed.json",
            mime="application/json",
            key=f"dl_ats_json_{json_hash}"
        )

    # Tab 6: Raw Extracted Text
    with tab_raw:
        render_html('<div class="tab-section-header">📄 Raw Extracted Text Stream</div>')
        st.text_area("Extracted Document Text", value=raw_text, height=350)


if __name__ == "__main__":
    main()
