"""Template Renderer for generating styled HTML resume previews."""

from typing import Any, Dict


def render_modern_two_column(data: Dict[str, Any]) -> str:
    """Render resume in a modern 2-column layout (matching Resume.io/Canva sidebar style)."""
    contact = data.get("contact", {})
    name = contact.get("name") or "Candidate Name"
    email = contact.get("email") or ""
    phone = contact.get("phone") or ""
    linkedin = contact.get("linkedin") or ""
    portfolio = contact.get("portfolio") or ""

    summary = data.get("summary", "")
    experience = data.get("experience", [])
    education = data.get("education", [])
    skills = data.get("skills", [])
    projects = data.get("projects", [])
    languages = data.get("languages", [])
    hobbies = data.get("hobbies", [])
    certifications = data.get("certifications", [])

    # Initial letter
    initials = name[0] if name else "C"

    # Skills HTML
    skills_html = "".join([f'<div class="skill-tag">{s}</div>' for s in skills])

    # Languages HTML
    lang_html = "".join([f'<div class="sidebar-item">{l}</div>' for l in languages])

    # Hobbies HTML
    hobbies_html = "".join([f'<div class="sidebar-item">{h}</div>' for h in hobbies])

    # Experience HTML
    exp_html = ""
    for exp in experience:
        title = exp.get("title") or "Role / Position"
        company = exp.get("company") or "Company"
        dates = exp.get("dates") or ""
        desc = exp.get("description") or ""
        desc_formatted = desc.replace("\n", "<br>")
        exp_html += f"""
        <div class="job-block">
            <div class="job-header">
                <span class="job-title">{title}</span>
                <span class="job-company">{f"at {company}" if company else ""}</span>
            </div>
            <div class="job-dates">{dates}</div>
            <div class="job-desc">{desc_formatted}</div>
        </div>
        """

    # Education HTML
    edu_html = ""
    for edu in education:
        deg = edu.get("degree") or "Degree / Program"
        inst = edu.get("institution") or "Institution"
        dates = edu.get("dates") or ""
        edu_html += f"""
        <div class="edu-block">
            <div class="edu-degree">{deg}</div>
            <div class="edu-inst">{inst}</div>
            <div class="edu-dates">{dates}</div>
        </div>
        """

    # Certifications HTML
    cert_html = ""
    for cert in certifications:
        c_name = cert.get("name") or ""
        cert_html += f'<div class="edu-block"><div class="edu-degree">{c_name}</div></div>'

    # Projects HTML
    proj_html = ""
    for proj in projects:
        p_name = proj.get("name") or "Project"
        p_desc = proj.get("description") or ""
        p_desc_formatted = p_desc.replace("\n", "<br>")
        proj_html += f"""
        <div class="job-block">
            <div class="job-title">{p_name}</div>
            <div class="job-desc">{p_desc_formatted}</div>
        </div>
        """

    top_role_display = experience[0].get("title", "") if experience else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        .resume-container {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #FFFFFF;
            color: #2D3748;
            max-width: 900px;
            margin: 0 auto;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #E2E8F0;
            overflow: hidden;
        }}
        .resume-top-banner {{
            background: #1A202C;
            color: #FFFFFF;
            padding: 30px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .top-name {{
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        .top-role {{
            font-size: 14px;
            color: #A0AEC0;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 4px;
        }}
        .resume-body {{
            display: flex;
            flex-direction: row;
        }}
        .sidebar {{
            width: 32%;
            background: #F7FAFC;
            border-right: 1px solid #EDF2F7;
            padding: 30px 25px;
        }}
        .main-content {{
            width: 68%;
            padding: 30px 35px;
        }}
        .sec-title-sidebar {{
            font-size: 12px;
            font-weight: 700;
            color: #4A5568;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-top: 25px;
            margin-bottom: 12px;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 4px;
        }}
        .sec-title-sidebar:first-child {{
            margin-top: 0;
        }}
        .sec-title-main {{
            font-size: 14px;
            font-weight: 700;
            color: #2B6CB0;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-top: 28px;
            margin-bottom: 14px;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 6px;
        }}
        .sec-title-main:first-child {{
            margin-top: 0;
        }}
        .sidebar-item {{
            font-size: 13px;
            color: #4A5568;
            margin-bottom: 6px;
            line-height: 1.4;
            word-break: break-word;
        }}
        .sidebar-item strong {{
            color: #2D3748;
        }}
        .skill-tag {{
            display: block;
            background: #EDF2F7;
            color: #2D3748;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 6px;
            border-left: 3px solid #3182CE;
        }}
        .job-block {{
            margin-bottom: 20px;
        }}
        .job-header {{
            display: flex;
            align-items: baseline;
            gap: 6px;
        }}
        .job-title {{
            font-size: 15px;
            font-weight: 700;
            color: #1A202C;
        }}
        .job-company {{
            font-size: 14px;
            font-weight: 600;
            color: #3182CE;
        }}
        .job-dates {{
            font-size: 12px;
            color: #718096;
            margin-top: 2px;
            margin-bottom: 6px;
            font-style: italic;
        }}
        .job-desc {{
            font-size: 13px;
            color: #4A5568;
            line-height: 1.55;
        }}
        .edu-block {{
            margin-bottom: 14px;
        }}
        .edu-degree {{
            font-size: 14px;
            font-weight: 700;
            color: #2D3748;
        }}
        .edu-inst {{
            font-size: 13px;
            color: #3182CE;
            font-weight: 500;
        }}
        .edu-dates {{
            font-size: 12px;
            color: #718096;
            font-style: italic;
        }}
        .summary-text {{
            font-size: 13.5px;
            line-height: 1.6;
            color: #4A5568;
        }}
    </style>
    </head>
    <body>
    <div class="resume-container">
        <div class="resume-top-banner">
            <div>
                <div class="top-name">{name}</div>
                {f'<div class="top-role">{top_role_display}</div>' if top_role_display else ''}
            </div>
        </div>
        <div class="resume-body">
            <div class="sidebar">
                <div class="sec-title-sidebar">Contact</div>
                {f'<div class="sidebar-item"><strong>Phone:</strong><br>{phone}</div>' if phone else ''}
                {f'<div class="sidebar-item"><strong>Email:</strong><br>{email}</div>' if email else ''}
                
                {f'<div class="sec-title-sidebar">Links</div>' if (linkedin or portfolio) else ''}
                {f'<div class="sidebar-item"><a href="{linkedin}" target="_blank" style="color:#3182CE;">LinkedIn</a></div>' if linkedin else ''}
                {f'<div class="sidebar-item"><a href="{portfolio}" target="_blank" style="color:#3182CE;">Portfolio</a></div>' if portfolio else ''}

                {f'<div class="sec-title-sidebar">Skills</div>{skills_html}' if skills else ''}
                {f'<div class="sec-title-sidebar">Languages</div>{lang_html}' if languages else ''}
                {f'<div class="sec-title-sidebar">Hobbies</div>{hobbies_html}' if hobbies else ''}
            </div>
            <div class="main-content">
                {f'<div class="sec-title-main">Profile</div><div class="summary-text">{summary}</div>' if summary else ''}
                {f'<div class="sec-title-main">Employment History</div>{exp_html}' if exp_html else ''}
                {f'<div class="sec-title-main">Education</div>{edu_html}' if edu_html else ''}
                {f'<div class="sec-title-main">Certifications</div>{cert_html}' if cert_html else ''}
                {f'<div class="sec-title-main">Projects</div>{proj_html}' if proj_html else ''}
            </div>
        </div>
    </div>
    </body>
    </html>
    """
    return html


def render_classic_executive(data: Dict[str, Any]) -> str:
    """Render resume in a clean, elegant single-column executive format."""
    contact = data.get("contact", {})
    name = contact.get("name") or "Candidate Name"
    email = contact.get("email") or ""
    phone = contact.get("phone") or ""
    linkedin = contact.get("linkedin") or ""
    portfolio = contact.get("portfolio") or ""

    summary = data.get("summary", "")
    experience = data.get("experience", [])
    education = data.get("education", [])
    skills = data.get("skills", [])
    projects = data.get("projects", [])
    languages = data.get("languages", [])
    hobbies = data.get("hobbies", [])
    certifications = data.get("certifications", [])

    contact_items = [item for item in [email, phone, linkedin, portfolio] if item]
    contact_line = " &nbsp;|&nbsp; ".join(contact_items)

    skills_joined = ", ".join(skills)
    lang_joined = ", ".join(languages)
    hobbies_joined = ", ".join(hobbies)

    exp_html = ""
    for exp in experience:
        title = exp.get("title") or ""
        company = exp.get("company") or ""
        dates = exp.get("dates") or ""
        desc = exp.get("description", "").replace("\n", "<br>")
        exp_html += f"""
        <div style="margin-bottom: 16px;">
            <div style="display:flex; justify-content:space-between; font-weight:700; color:#1A202C;">
                <span>{title} {f"— {company}" if company else ""}</span>
                <span style="font-weight:600; color:#718096; font-size:13px;">{dates}</span>
            </div>
            <div style="font-size:13.5px; color:#4A5568; margin-top:4px; line-height:1.55;">{desc}</div>
        </div>
        """

    edu_html = ""
    for edu in education:
        deg = edu.get("degree") or ""
        inst = edu.get("institution") or ""
        dates = edu.get("dates") or ""
        edu_html += f"""
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <div><strong>{deg}</strong> {f", {inst}" if inst else ""}</div>
            <div style="color:#718096; font-size:13px;">{dates}</div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        .exec-container {{
            font-family: 'Georgia', serif;
            background: #FFFFFF;
            color: #1A202C;
            max-width: 850px;
            margin: 0 auto;
            padding: 40px 50px;
            border-radius: 6px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
            border: 1px solid #E2E8F0;
        }}
        .exec-name {{
            font-size: 26px;
            font-weight: bold;
            text-align: center;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        .exec-contact {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            text-align: center;
            font-size: 13px;
            color: #4A5568;
            margin-top: 6px;
            margin-bottom: 20px;
            border-bottom: 1px solid #CBD5E0;
            padding-bottom: 12px;
        }}
        .exec-section {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #2D3748;
            border-bottom: 1.5px solid #2D3748;
            padding-bottom: 3px;
            margin-top: 22px;
            margin-bottom: 12px;
        }}
        .exec-body {{
            font-size: 14px;
            line-height: 1.6;
            color: #2D3748;
        }}
    </style>
    </head>
    <body>
    <div class="exec-container">
        <div class="exec-name">{name}</div>
        <div class="exec-contact">{contact_line}</div>
        
        {f'<div class="exec-section">Executive Summary</div><div class="exec-body">{summary}</div>' if summary else ''}
        {f'<div class="exec-section">Experience</div>{exp_html}' if exp_html else ''}
        {f'<div class="exec-section">Education</div>{edu_html}' if edu_html else ''}
        {f'<div class="exec-section">Skills & Expertise</div><div class="exec-body">{skills_joined}</div>' if skills_joined else ''}
        {f'<div class="exec-section">Languages</div><div class="exec-body">{lang_joined}</div>' if lang_joined else ''}
        {f'<div class="exec-section">Hobbies & Interests</div><div class="exec-body">{hobbies_joined}</div>' if hobbies_joined else ''}
    </div>
    </body>
    </html>
    """
