from flask import Flask, request, jsonify
import pdfplumber
from docx import Document
import re
from nltk.corpus import stopwords
import nltk
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

nltk.download('stopwords')  # Run this once

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resume_analyzer.db'  # SQLite
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_keywords = db.Column(db.JSON)

# Initialize DB (run once)
with app.app_context():
    db.create_all()

@app.route('/parse-resume', methods=['POST'])
def parse_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    text = ""

    try:
        if file.filename.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages])
        elif file.filename.endswith('.docx'):
            doc = Document(file)
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        keywords = extract_keywords(text)
        return jsonify({"text": text, "keywords": keywords})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    words = re.findall(r'\w+', text.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 3]
    return keywords

@app.route('/compare', methods=['POST'])
def compare():
    data = request.json
    resume_keywords = set(data.get('resume_keywords', []))
    job_description = data.get('job_description', "")
    
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    # Extract keywords from job description
    job_keywords = set(extract_keywords(job_description))
    matches = list(job_keywords & resume_keywords)
    missing = list(job_keywords - resume_keywords)

    return jsonify({"matches": matches, "missing": missing})

@app.route('/save-analysis', methods=['POST'])
def save_analysis():
    data = request.json
    try:
        new_entry = User(resume_keywords=data['keywords'])
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"message": "Analysis saved!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to the Resume Analyzer API!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Allow external connections