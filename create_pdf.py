from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
import io
import streamlit as st

def create_pdf(applicant_data):
    """Generate a professional PDF resume with the requested changes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#333333"),  # Dark gray
        spaceAfter=10,
        alignment=TA_CENTER  # Center alignment for title
    )
    position_style = ParagraphStyle(
        'CustomPosition',
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=14,
        textColor=colors.HexColor("#555555"),  # Medium gray
        spaceAfter=20,
        alignment=TA_CENTER  # Center alignment for position
    )
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=12,
        textColor=colors.HexColor("#444444"),  # Dark gray
        spaceAfter=10,
        alignment=TA_CENTER  # Center alignment for email and mobile
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#444444"),  # Slightly lighter gray
        spaceAfter=10,
        alignment=TA_LEFT
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.black,
        alignment=TA_JUSTIFY  # Justify text for summary
    )
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=normal_style,
        bulletIndent=10,
    )

    story = []

    # Header section
    story.append(Paragraph(applicant_data["name"], title_style))
    story.append(Paragraph(applicant_data["position"], position_style))
    story.append(Paragraph(f"Email: {applicant_data['email']} | Mobile: {applicant_data['mobile']}", contact_style))
    story.append(Spacer(1, 20))

    # Professional Summary
    story.append(Paragraph("Professional Summary", subtitle_style))
    story.append(Paragraph(applicant_data["generated_prof_summary"], normal_style))
    story.append(Spacer(1, 12))

    # Experience
    story.append(Paragraph("Experience", subtitle_style))
    for exp in applicant_data["experience"]:
        story.append(Paragraph(f"{exp.get('company', 'Not found')}", normal_style))
        story.append(Paragraph(f"{exp.get('position', 'Not found')}", normal_style))
        story.append(Paragraph(f"{exp.get('duration', 'Not found')}", normal_style))
        story.append(Paragraph("", normal_style))
        job_list = ListFlowable(
            [ListItem(Paragraph(desc, bullet_style)) for desc in exp.get("job_descriptions", ["Not found"])],
            bulletType="bullet",
            bulletFontName="Helvetica-Bold",
            bulletFontSize=10
        )
        story.append(job_list)
        story.append(Spacer(1, 12))

    # Education
    story.append(Paragraph("Education", subtitle_style))
    education_list = ListFlowable(
        [ListItem(Paragraph(edu, normal_style)) for edu in applicant_data["education"]],
        bulletType="bullet",
        bulletFontName="Helvetica-Bold",
        bulletFontSize=10
    )
    story.append(education_list)
    story.append(Spacer(1, 12))

    # Achievements
    if "achievements" in applicant_data and applicant_data["achievements"] != ["Not found"]:
        story.append(Paragraph("Achievements", subtitle_style))
        achievements_list = ListFlowable(
            [ListItem(Paragraph(achievement, normal_style)) for achievement in applicant_data["achievements"]],
            bulletType="bullet",
            bulletFontName="Helvetica-Bold",
            bulletFontSize=10
        )
        story.append(achievements_list)
        story.append(Spacer(1, 12))

    # Add footer or final space
    story.append(Spacer(1, 30))

    # Build PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def create_resume():
    """Create PDF page with form to input resume data."""
    st.title("Create PDF Resume")

    # Load session data into applicant_data
    applicant_data = {
        "name": st.session_state.get("name", ""),
        "email": st.session_state.get("email", ""),
        "mobile": st.session_state.get("mobile", ""),
        "generated_prof_summary": st.session_state.get("generated_prof_summary", ""),
        "education": st.session_state.get("education", []),
        "experience": st.session_state.get("updated_experience", []),  # This should be a list of dicts
        "skills": st.session_state.get("updated_skills", []),
        "achievements": st.session_state.get("special_achievements", []),
        "position": st.session_state.get("position", ""),
    }

    # Form for resume data
    with st.form("resume_form"):
        st.subheader("Personal Information")
        applicant_data["name"] = st.text_input("Full Name", value=applicant_data["name"])
        applicant_data["email"] = st.text_input("Email", value=applicant_data["email"])
        applicant_data["mobile"] = st.text_input("Mobile", value=applicant_data["mobile"])

        st.subheader("Professional Summary")
        applicant_data["generated_prof_summary"] = st.text_area("Summary", value=applicant_data["generated_prof_summary"])

        st.subheader("Skills")
        applicant_data["skills"] = st.text_area("Skills (comma-separated)", value=", ".join(applicant_data["skills"])).split(", ")

        st.subheader("Experience")
        experience_entries = []
        for idx, exp in enumerate(applicant_data["experience"], start=1):
            st.write(f"### Job {idx}")
            company = st.text_input(f"Company {idx}", value=exp.get('company', ''))
            position = st.text_input(f"Position {idx}", value=exp.get('position', ''))
            duration = st.text_input(f"Duration {idx}", value=exp.get('duration', ''))
            job_descriptions = st.text_area(f"Responsibilities for {idx} (one per line)", value="\n".join(exp.get('job_descriptions', [])))

            # Collect the experience entry
            experience_entries.append({
                "company": company,
                "position": position,
                "duration": duration,
                "job_descriptions": job_descriptions.splitlines()  # Split by new lines
            })

        applicant_data["experience"] = experience_entries  # Update the applicant_data with the new experience entries

        st.subheader("Education")
        applicant_data["education"] = st.text_area("Education (one per line)", value="\n".join(applicant_data["education"])).split("\n")

        st.subheader("Achievements")
        applicant_data["achievements"] = st.text_area("Achievements (one per line)", value="\n".join(applicant_data["achievements"])).split("\n")

        # Submit button for the form
        submitted = st.form_submit_button("Generate PDF")

    if submitted:
            # Create PDF
        pdf = create_pdf(applicant_data)

            # Provide download link
        st.download_button(
                label="Download Resume PDF",
                data=pdf,
                file_name=f"{applicant_data['name'].lower().replace(' ', '_')}_resume.pdf",
                mime="application/pdf"
            )
