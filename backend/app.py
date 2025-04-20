from flask import Flask, request, jsonify
import pdfplumber
from docx import Document
import re
from nltk.corpus import stopwords
import nltk
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from flask_cors import CORS
import boto3
import os
from datetime import datetime
from dotenv import load_dotenv
import secrets
import logging
from werkzeug.utils import secure_filename
from sqlalchemy import text

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file size limit
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# S3 Configuration
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
s3 = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    config=boto3.session.Config(signature_version='s3v4')
)

# Database Model
class Analysis(db.Model):
    __tablename__ = 'analyses'
    id = db.Column(db.Integer, primary_key=True)
    resume_keywords = db.Column(db.JSON, nullable=False)
    s3_key = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_ip = db.Column(db.String(45))  # Store IPv4/IPv6 addresses

# Helper Functions
def extract_keywords(text):
    """Enhanced keyword extraction with error handling"""
    try:
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('english'))
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())  # Better word matching
        keywords = [
            word for word in words 
            if word not in stop_words 
            and len(word) > 3 
            and not word.isnumeric()
        ]
        return list(set(keywords))  # Remove duplicates
    except Exception as e:
        logger.error(f"Keyword extraction error: {str(e)}")
        return []

def validate_file(file):
    """Secure file validation"""
    if not file:
        raise ValueError("No file provided")
    
    filename = secure_filename(file.filename)
    if not filename:
        raise ValueError("Invalid filename")
    
    ext = filename.split('.')[-1].lower()
    if ext not in {'pdf', 'docx'}:
        raise ValueError("Only PDF and DOCX files are allowed")
    
    return filename, ext

def upload_to_s3(file):
    """Secure S3 upload with validation"""
    filename, ext = validate_file(file)
    
    # Generate secure path
    s3_key = (
        f"uploads/{filename}/{datetime.now().strftime('%Y/%m/%d')}/"
        f"{secrets.token_hex(8)}.{ext}"
    )
    
    try:
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': (
                    'application/pdf' if ext == 'pdf' 
                    else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ),
                'ACL': 'private',
                'ServerSideEncryption': 'AES256'
            }
        )
        return s3_key
    except Exception as e:
        logger.error(f"S3 upload failed: {str(e)}")
        raise

# API Endpoints
@app.route('/parse-resume', methods=['POST'])
def parse_resume():
    """Secure resume parsing endpoint"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    try:
        # File processing
        text = ""
        if file.filename.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        elif file.filename.endswith('.docx'):
            doc = Document(file)
            text = "\n".join(para.text for para in doc.paragraphs)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        # Store and analyze
        s3_key = upload_to_s3(file)
        keywords = extract_keywords(text)
        
        # Save to DB
        analysis = Analysis(
            resume_keywords=keywords,
            s3_key=s3_key,
            user_ip=request.remote_addr
        )
        db.session.add(analysis)
        db.session.commit()

        # Generate presigned URL
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600
        )

        return jsonify({
            "analysis_id": analysis.id,
            "keywords": keywords,
            "resume_url": presigned_url,
            "text_preview": text[:1000]  # Return limited text
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/compare', methods=['POST'])
def compare_keywords():
    """Job description comparison endpoint"""
    try:
        data = request.get_json()
        if not data or 'job_description' not in data:
            raise ValueError("Invalid request data")

        resume_keywords = set(data.get('resume_keywords', []))
        job_keywords = set(extract_keywords(data['job_description']))
        
        return jsonify({
            "matches": sorted(list(job_keywords & resume_keywords)),
            "missing": sorted(list(job_keywords - resume_keywords)),
            "score": len(job_keywords & resume_keywords) / max(len(job_keywords), 1) * 100
        })
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        return jsonify({"error": "Comparison failed"}), 500

@app.route('/analysis/<int:analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """Analysis retrieval endpoint"""
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
        logger.error(f"Retrieval error: {str(e)}")
        return jsonify({"error": "Analysis not found"}), 404

# Health endpoints
@app.route('/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG') == 'True')