from flask import Flask, request, jsonify
import pdfplumber
from docx import Document
import re
from nltk.corpus import stopwords
import nltk
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import boto3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resume_analyzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file size limit
db = SQLAlchemy(app)

# S3 Configuration
S3_BUCKET = os.getenv('S3_BUCKET', 'resume-analyzer-files')
S3_REGION = os.getenv('S3_REGION', 'eu-north-1')
s3 = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)

# Database Model
class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_keywords = db.Column(db.JSON)
    s3_key = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize DB
with app.app_context():
    db.create_all()

# Helper Functions
def extract_keywords(text):
    """Extract keywords from text using NLP techniques"""
    try:
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('english'))
        words = re.findall(r'\w+', text.lower())
        return [word for word in words 
                if word not in stop_words 
                and len(word) > 3 
                and not word.isnumeric()]
    except Exception as e:
        app.logger.error(f"Keyword extraction failed: {str(e)}")
        return []

def upload_to_s3(file):
    """Upload file to S3 and return secure URL"""
    try:
        file_key = f"uploads/{datetime.now().timestamp()}-{file.filename}"
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            file_key,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'private'  # For security, we'll use pre-signed URLs
            }
        )
        return file_key
    except Exception as e:
        app.logger.error(f"S3 upload failed: {str(e)}")
        raise

# API Endpoints
@app.route('/parse-resume', methods=['POST'])
def parse_resume():
    """Endpoint for resume parsing and analysis"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        # File parsing
        text = ""
        if file.filename.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        elif file.filename.endswith('.docx'):
            doc = Document(file)
            text = "\n".join(para.text for para in doc.paragraphs)
        else:
            return jsonify({"error": "Unsupported file type. Use PDF or DOCX"}), 400

        # Store in S3
        s3_key = upload_to_s3(file)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600  # 1-hour access
        )

        # Analysis
        keywords = extract_keywords(text)
        
        # Save to database
        analysis = Analysis(
            resume_keywords=keywords,
            s3_key=s3_key
        )
        db.session.add(analysis)
        db.session.commit()

        return jsonify({
            "text": text[:5000] + "..." if len(text) > 5000 else text,  # Limit response size
            "keywords": keywords,
            "resume_url": presigned_url,
            "analysis_id": analysis.id
        })

    except Exception as e:
        app.logger.error(f"Resume parsing failed: {str(e)}")
        return jsonify({"error": "Processing failed. Please try again."}), 500

@app.route('/compare', methods=['POST'])
def compare():
    """Compare resume keywords with job description"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    resume_keywords = set(data.get('resume_keywords', []))
    job_description = data.get('job_description', "")

    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    try:
        job_keywords = set(extract_keywords(job_description))
        return jsonify({
            "matches": sorted(list(job_keywords & resume_keywords)),
            "missing": sorted(list(job_keywords - resume_keywords))
        })
    except Exception as e:
        app.logger.error(f"Comparison failed: {str(e)}")
        return jsonify({"error": "Comparison failed"}), 500

@app.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Retrieve previous analysis"""
    try:
        analysis = Analysis.query.get_or_404(analysis_id)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': analysis.s3_key},
            ExpiresIn=3600
        )
        return jsonify({
            "id": analysis.id,
            "keywords": analysis.resume_keywords,
            "resume_url": presigned_url,
            "created_at": analysis.created_at.isoformat()
        })
    except Exception as e:
        app.logger.error(f"Analysis retrieval failed: {str(e)}")
        return jsonify({"error": "Analysis not found"}), 404

# Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'False') == 'True')