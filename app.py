from flask import Flask, render_template, request
import re

app = Flask(__name__)


def analyze_resume(text):
    text_lower = text.lower()

    skills = {
        "Python": ["python"],
        "JavaScript": ["javascript", "js"],
        "HTML": ["html"],
        "CSS": ["css"],
        "SQL": ["sql", "mysql", "postgresql"],
        "React": ["react", "reactjs"],
        "Java": ["java"],
        "C++": ["c++"],
        "Excel": ["excel", "microsoft excel"],
        "Machine Learning": ["machine learning", "ml"],
        "Data Analysis": ["data analysis", "data analytics"],
    }

    found_skills = []

    for skill, keywords in skills.items():
        if any(keyword in text_lower for keyword in keywords):
            found_skills.append(skill)

    total_skills = len(skills)
    score = int((len(found_skills) / total_skills) * 100)

    if score >= 70:
        recommendation = "Excellent skill coverage. Your resume has a strong technical profile."
    elif score >= 40:
        recommendation = "Good profile. Add more relevant technical skills and projects."
    else:
        recommendation = "Improve your resume by adding relevant technical skills, projects and certifications."

    return {
        "skills": found_skills,
        "score": score,
        "recommendation": recommendation
    }


@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        resume_text = request.form.get("resume_text", "")
        result = analyze_resume(resume_text)

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
