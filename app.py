
  from flask import Flask, render_template, request
import re
from pathlib import Path

app = Flask(__name__)

# Skill database grouped by career area.
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
    "Data Analysis": ["data analysis", "data analytics", "data analyst"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "NLP": ["natural language processing", "nlp"],
    "Git/GitHub": ["git", "github"],
    "REST API": ["rest api", "restful api", "api"],
    "MongoDB": ["mongodb", "mongo db"],
    "Flask": ["flask"],
    "Django": ["django"],
}

ROLE_SKILLS = {
    "Data Analyst": ["Python", "SQL", "Excel", "Power BI", "Tableau", "Data Analysis"],
    "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Git/GitHub", "REST API"],
    "Python Developer": ["Python", "SQL", "Flask", "Django", "Git/GitHub", "REST API"],
    "Software Developer": ["Python", "Java", "SQL", "Git/GitHub", "REST API"],
    "ML Engineer": ["Python", "SQL", "Machine Learning", "Deep Learning", "NLP", "Git/GitHub"],
}

def normalize(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def extract_skills(text):
    low = normalize(text)
    found = []
    for skill, keywords in SKILL_DB.items():
        if any(re.search(r"(?<!\w)" + re.escape(k.lower()) + r"(?!\w)", low) for k in keywords):
            found.append(skill)
    return found

def section_flags(text):
    low = normalize(text)
    sections = {
        "Contact": any(x in low for x in ["email", "phone", "linkedin", "github"]),
        "Summary": any(x in low for x in ["summary", "profile", "objective"]),
        "Education": "education" in low,
        "Experience": any(x in low for x in ["experience", "internship", "employment"]),
        "Projects": "project" in low,
        "Skills": "skills" in low,
        "Certifications": any(x in low for x in ["certification", "certifications", "certificate"]),
    }
    return sections

def analyze_resume(text, role):
    text = text or ""
    skills = extract_skills(text)
    sections = section_flags(text)

    target = ROLE_SKILLS.get(role, ROLE_SKILLS["Data Analyst"])
    matched = [s for s in target if s in skills]
    missing = [s for s in target if s not in skills]

    skill_score = round((len(skills) / len(SKILL_DB)) * 100)
    role_score = round((len(matched) / len(target)) * 100) if target else 0

    section_score = round((sum(sections.values()) / len(sections)) * 100)
    length_score = 100 if 400 <= len(text.split()) <= 900 else 70 if len(text.split()) >= 250 else 40

    ats_score = round((role_score * 0.50) + (section_score * 0.30) + (length_score * 0.20))

    suggestions = []
    if not sections["Contact"]:
        suggestions.append("Add professional contact details, LinkedIn and GitHub.")
    if not sections["Projects"]:
        suggestions.append("Add 1–3 measurable projects with technologies and outcomes.")
    if not sections["Experience"]:
        suggestions.append("Add internship, training, freelance or practical experience if available.")
    if not sections["Certifications"]:
        suggestions.append("Add relevant certifications or training.")
    if missing:
        suggestions.append("For the selected role, consider adding: " + ", ".join(missing) + ".")
    if len(text.split()) < 250:
        suggestions.append("Your resume text is short. Add stronger project, education and achievement details.")
    if len(text.split()) > 1000:
        suggestions.append("Your resume may be too long. Keep bullets concise and job-focused.")

    if ats_score >= 80:
        verdict = "Excellent match"
    elif ats_score >= 60:
        verdict = "Good match"
    else:
        verdict = "Needs improvement"

    return {
        "ats_score": ats_score,
        "skill_score": skill_score,
        "role_score": role_score,
        "skills": skills,
        "matched": matched,
        "missing": missing,
        "sections": sections,
        "suggestions": suggestions,
        "verdict": verdict,
        "role": role,
        "word_count": len(text.split()),
    }

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None
    resume_text = ""

    if request.method == "POST":
        role = request.form.get("role", "Data Analyst")
        resume_text = request.form.get("resume_text", "").strip()
        upload = request.files.get("resume_file")

        if upload and upload.filename:
            ext = Path(upload.filename).suffix.lower()
            try:
                data = upload.read()
                if ext == ".txt":
                    resume_text = data.decode("utf-8", errors="ignore")
                elif ext == ".pdf":
                    from pypdf import PdfReader
                    reader = PdfReader(__import__("io").BytesIO(data))
                    resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                elif ext == ".docx":
                    from docx import Document
                    doc = Document(__import__("io").BytesIO(data))
                    resume_text = "\n".join(p.text for p in doc.paragraphs)
                else:
                    error = "Supported files: PDF, DOCX and TXT."
            except Exception as exc:
                error = f"Could not read the file: {exc}"

        if not resume_text:
            error = error or "Please paste resume text or upload a resume file."
        else:
            result = analyze_resume(resume_text, role)

    return render_template("index.html", result=result, error=error, resume_text=resume_text)

if __name__ == "__main__":
    app.run(debug=True)