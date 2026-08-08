
  from flask import Flask, render_template, request
import re
from pathlib import Path
import io

app = Flask(__name__)

# --------------------------------------------------
# Skill Database
# --------------------------------------------------

SKILL_DB = {
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "React": ["react", "reactjs"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "Java": ["java"],
    "C++": ["c++"],
    "SQL": ["sql", "mysql", "postgresql", "postgres"],
    "Excel": ["excel", "microsoft excel"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Data Analysis": [
        "data analysis",
        "data analytics",
        "data analyst"
    ],
    "Machine Learning": [
        "machine learning",
        "ml"
    ],
    "Deep Learning": ["deep learning"],
    "NLP": [
        "natural language processing",
        "nlp"
    ],
    "Git/GitHub": ["git", "github"],
    "REST API": [
        "rest api",
        "restful api",
        "api"
    ],
    "MongoDB": [
        "mongodb",
        "mongo db"
    ],
    "Flask": ["flask"],
    "Django": ["django"],
}

# --------------------------------------------------
# Job Role Skills
# --------------------------------------------------

ROLE_SKILLS = {
    "Data Analyst": [
        "Python",
        "SQL",
        "Excel",
        "Power BI",
        "Tableau",
        "Data Analysis"
    ],

    "Web Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Git/GitHub",
        "REST API"
    ],

    "Python Developer": [
        "Python",
        "SQL",
        "Flask",
        "Django",
        "Git/GitHub",
        "REST API"
    ],

    "Software Developer": [
        "Python",
        "Java",
        "SQL",
        "Git/GitHub",
        "REST API"
    ],

    "ML Engineer": [
        "Python",
        "SQL",
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Git/GitHub"
    ],
}


# --------------------------------------------------
# Text Normalization
# --------------------------------------------------

def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        (text or "").lower()
    ).strip()


# --------------------------------------------------
# Extract Skills
# --------------------------------------------------

def extract_skills(text):
    low = normalize(text)
    found = []

    for skill, keywords in SKILL_DB.items():

        for keyword in keywords:

            pattern = (
                r"(?<!\w)"
                + re.escape(keyword.lower())
                + r"(?!\w)"
            )

            if re.search(pattern, low):
                found.append(skill)
                break

    return found


# --------------------------------------------------
# Resume Section Detection
# --------------------------------------------------

def section_flags(text):

    low = normalize(text)

    sections = {

        "Contact": any(
            x in low
            for x in [
                "email",
                "phone",
                "linkedin",
                "github"
            ]
        ),

        "Summary": any(
            x in low
            for x in [
                "summary",
                "profile",
                "objective"
            ]
        ),

        "Education": "education" in low,

        "Experience": any(
            x in low
            for x in [
                "experience",
                "internship",
                "employment"
            ]
        ),

        "Projects": "project" in low,

        "Skills": "skills" in low,

        "Certifications": any(
            x in low
            for x in [
                "certification",
                "certifications",
                "certificate"
            ]
        ),
    }

    return sections


# --------------------------------------------------
# Resume Analysis
# --------------------------------------------------

def analyze_resume(text, role):

    text = text or ""

    skills = extract_skills(text)

    sections = section_flags(text)

    target = ROLE_SKILLS.get(
        role,
        ROLE_SKILLS["Data Analyst"]
    )

    # Matching skills
    matched = [
        skill
        for skill in target
        if skill in skills
    ]

    # Missing skills
    missing = [
        skill
        for skill in target
        if skill not in skills
    ]

    # Skill score
    skill_score = round(
        (len(skills) / len(SKILL_DB)) * 100
    )

    skill_score = min(skill_score, 100)

    # Role match score
    role_score = (
        round(
            (len(matched) / len(target)) * 100
        )
        if target
        else 0
    )

    # Resume section score
    section_score = round(
        (
            sum(sections.values())
            / len(sections)
        ) * 100
    )

    # Resume length score
    word_count = len(text.split())

    if 400 <= word_count <= 900:
        length_score = 100

    elif word_count >= 250:
        length_score = 70

    else:
        length_score = 40

    # ATS-style score
    ats_score = round(
        (role_score * 0.50)
        + (section_score * 0.30)
        + (length_score * 0.20)
    )

    # --------------------------------------------------
    # Recommendations
    # --------------------------------------------------

    suggestions = []

    if not sections["Contact"]:
        suggestions.append(
            "Add professional contact details, "
            "LinkedIn and GitHub."
        )

    if not sections["Summary"]:
        suggestions.append(
            "Add a short professional summary "
            "or career objective."
        )

    if not sections["Skills"]:
        suggestions.append(
            "Add a dedicated technical skills section."
        )

    if not sections["Projects"]:
        suggestions.append(
            "Add 1–3 projects with technologies "
            "and measurable outcomes."
        )

    if not sections["Experience"]:
        suggestions.append(
            "Add internship, training, freelance "
            "or practical experience if available."
        )

    if not sections["Certifications"]:
        suggestions.append(
            "Add relevant certifications or training."
        )

    if missing:
        suggestions.append(
            "For the selected role, consider adding: "
            + ", ".join(missing)
            + "."
        )

    if word_count < 250:
        suggestions.append(
            "Your resume is short. Add stronger "
            "project, education and achievement details."
        )

    if word_count > 1000:
        suggestions.append(
            "Your resume may be too long. "
            "Keep bullets concise and job-focused."
        )

    # --------------------------------------------------
    # Verdict
    # --------------------------------------------------

    if ats_score >= 80:
        verdict = "Excellent Match"

    elif ats_score >= 60:
        verdict = "Good Match"

    else:
        verdict = "Needs Improvement"

    # --------------------------------------------------
    # Final Result
    # --------------------------------------------------

    return {

        # Main ATS score
        "ats_score": ats_score,

        # Compatibility with old HTML
        "score": ats_score,

        # Other scores
        "skill_score": skill_score,
        "role_score": role_score,
        "section_score": section_score,
        "length_score": length_score,

        # Skills
        "skills": skills,
        "matched": matched,
        "missing": missing,

        # Sections
        "sections": sections,

        # Suggestions
        "suggestions": suggestions,

        # Result information
        "verdict": verdict,
        "role": role,
        "word_count": word_count,
    }


# --------------------------------------------------
# Extract Resume File
# --------------------------------------------------

def extract_file_text(upload):

    if not upload or not upload.filename:
        return ""

    ext = Path(upload.filename).suffix.lower()

    data = upload.read()

    # TXT
    if ext == ".txt":

        return data.decode(
            "utf-8",
            errors="ignore"
        )

    # PDF
    elif ext == ".pdf":

        from pypdf import PdfReader

        reader = PdfReader(
            io.BytesIO(data)
        )

        text = []

        for page in reader.pages:

            text.append(
                page.extract_text() or ""
            )

        return "\n".join(text)

    # DOCX
    elif ext == ".docx":

        from docx import Document

        document = Document(
            io.BytesIO(data)
        )

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    else:

        raise ValueError(
            "Supported files are PDF, DOCX and TXT."
        )


# --------------------------------------------------
# Home Route
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    result = None
    error = None
    resume_text = ""

    role = "Data Analyst"

    if request.method == "POST":

        role = request.form.get(
            "role",
            "Data Analyst"
        )

        resume_text = request.form.get(
            "resume_text",
            ""
        ).strip()

        upload = request.files.get(
            "resume_file"
        )

        # Try uploaded file first
        if upload and upload.filename:

            try:

                resume_text = extract_file_text(
                    upload
                )

            except Exception as exc:

                error = (
                    f"Could not read the file: {exc}"
                )

        # Validate resume
        if not resume_text:

            error = (
                error
                or
                "Please paste resume text "
                "or upload a resume file."
            )

        else:

            result = analyze_resume(
                resume_text,
                role
            )

    return render_template(
        "index.html",
        result=result,
        error=error,
        resume_text=resume_text,
        role=role,
        roles=ROLE_SKILLS.keys()
    )


# --------------------------------------------------
# Run Application
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )

 