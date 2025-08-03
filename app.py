import os
import json
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
from docx import Document
import re
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return text

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading TXT: {e}")
    return text

def extract_resume_text(file_path):
    """Extract text from resume file based on extension"""
    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_path)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_path)
    else:
        return ""

def get_role_specific_keywords(role):
    """Get role-specific keywords for better scoring"""
    role_keywords = {
        'software engineer': [
            'programming', 'coding', 'debugging', 'algorithms', 'data structures',
            'git', 'version control', 'testing', 'deployment', 'frameworks',
            'databases', 'apis', 'agile', 'scrum', 'ci/cd'
        ],
        'data scientist': [
            'machine learning', 'statistics', 'python', 'r', 'sql', 'data analysis',
            'visualization', 'modeling', 'algorithms', 'big data', 'pandas',
            'numpy', 'scikit-learn', 'tensorflow', 'pytorch'
        ],
        'product manager': [
            'roadmap', 'stakeholder', 'requirements', 'user stories', 'metrics',
            'analytics', 'market research', 'competitive analysis', 'strategy',
            'prioritization', 'cross-functional', 'agile', 'scrum'
        ],
        'marketing manager': [
            'campaigns', 'branding', 'digital marketing', 'seo', 'sem', 'social media',
            'content marketing', 'analytics', 'roi', 'lead generation', 'conversion',
            'market research', 'customer acquisition'
        ],
        'sales representative': [
            'prospecting', 'lead generation', 'closing', 'negotiation', 'crm',
            'pipeline', 'quota', 'territory', 'customer relationship', 'revenue',
            'presentations', 'cold calling', 'networking'
        ],
        'business analyst': [
            'requirements gathering', 'process improvement', 'stakeholder management',
            'documentation', 'workflow', 'analysis', 'reporting', 'sql', 'excel',
            'business intelligence', 'process mapping', 'gap analysis'
        ],
        'project manager': [
            'project planning', 'risk management', 'budget management', 'timeline',
            'milestone', 'stakeholder communication', 'resource allocation',
            'pmp', 'agile', 'scrum', 'gantt', 'project lifecycle'
        ],
        'designer': [
            'ui/ux', 'user experience', 'wireframes', 'prototyping', 'design thinking',
            'user research', 'adobe', 'figma', 'sketch', 'visual design',
            'typography', 'color theory', 'responsive design'
        ]
    }
    
    # Default keywords if role not found
    default_keywords = [
        'project', 'management', 'leadership', 'team', 'development',
        'analysis', 'communication', 'problem-solving', 'results',
        'achievement', 'improvement', 'collaboration'
    ]
    
    role_lower = role.lower()
    for key, keywords in role_keywords.items():
        if key in role_lower or any(word in role_lower for word in key.split()):
            return keywords + default_keywords
    
    return default_keywords

def calculate_ats_score(resume_text, role="general"):
    """Calculate ATS score based on various factors and role-specific criteria"""
    score = 0
    factors = {}
    
    # Check for contact information (20 points)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    
    if re.search(email_pattern, resume_text):
        score += 10
        factors['email'] = True
    else:
        factors['email'] = False
        
    if re.search(phone_pattern, resume_text):
        score += 10
        factors['phone'] = True
    else:
        factors['phone'] = False
    
    # Check for professional sections (40 points)
    sections = ['experience', 'education', 'skills', 'summary', 'objective']
    section_score = 0
    factors['sections_found'] = []
    
    for section in sections:
        if re.search(rf'\b{section}\b', resume_text, re.IGNORECASE):
            section_score += 8
            factors['sections_found'].append(section)
    
    score += min(section_score, 40)
    
    # Check for role-specific keywords and technical terms (25 points)
    role_keywords = get_role_specific_keywords(role)
    
    keyword_count = 0
    factors['keywords_found'] = []
    
    for keyword in role_keywords:
        if re.search(rf'\b{keyword}\b', resume_text, re.IGNORECASE):
            keyword_count += 1
            factors['keywords_found'].append(keyword)
    
    score += min(keyword_count * 2, 25)
    
    # Check for quantifiable achievements (15 points)
    number_pattern = r'\b\d+%|\b\d+\s*(million|thousand|k|m)\b|\$\d+|\b\d+\s*years?\b'
    numbers_found = len(re.findall(number_pattern, resume_text, re.IGNORECASE))
    score += min(numbers_found * 3, 15)
    factors['quantifiable_achievements'] = numbers_found
    
    factors['total_score'] = score
    factors['role'] = role
    return score, factors

def get_ai_suggestions(resume_text, score, factors):
    """Get AI-powered suggestions using Gemini API with role-specific analysis"""
    try:
        role = factors.get('role', 'general')
        prompt = f"""
        Analyze this resume for a {role} position and provide specific, actionable suggestions for improvement.
        
        Resume Text:
        {resume_text[:3000]}  # Limit text to avoid token limits
        
        Target Role: {role}
        Current ATS Score: {score}/100
        
        Analysis Factors:
        - Email present: {factors.get('email', False)}
        - Phone present: {factors.get('phone', False)}
        - Sections found: {factors.get('sections_found', [])}
        - Role-specific keywords found: {factors.get('keywords_found', [])}
        - Quantifiable achievements: {factors.get('quantifiable_achievements', 0)}
        
        Please provide role-specific suggestions:
        1. Top 5 improvements tailored for {role} positions to increase ATS score
        2. Missing sections or information crucial for {role} roles
        3. Role-specific keyword optimization (technical skills, industry terms)
        4. Formatting recommendations for {role} applications
        5. Content enhancement suggestions specific to {role} requirements
        6. Industry-specific achievements and metrics to highlight
        7. Skills and certifications relevant to {role} that might be missing
        
        Format your response as structured suggestions with clear, actionable items specifically tailored for {role} positions.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error generating AI suggestions: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['resume']
    role = request.form.get('role', 'general')  # Get role from form data
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text from resume
        resume_text = extract_resume_text(file_path)
        
        if not resume_text.strip():
            os.remove(file_path)  # Clean up
            return jsonify({'error': 'Could not extract text from file'}), 400
        
        # Calculate ATS score with role-specific analysis
        score, factors = calculate_ats_score(resume_text, role)
        
        # Get AI suggestions
        ai_suggestions = get_ai_suggestions(resume_text, score, factors)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'score': score,
            'factors': factors,
            'suggestions': ai_suggestions,
            'filename': file.filename,
            'role': role
        })
    
    return jsonify({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT files.'}), 400

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """Analyze resume text directly without file upload"""
    data = request.get_json()
    resume_text = data.get('text', '')
    role = data.get('role', 'general')  # Get role from JSON data
    
    if not resume_text.strip():
        return jsonify({'error': 'No text provided'}), 400
    
    # Calculate ATS score with role-specific analysis
    score, factors = calculate_ats_score(resume_text, role)
    
    # Get AI suggestions
    ai_suggestions = get_ai_suggestions(resume_text, score, factors)
    
    return jsonify({
        'success': True,
        'score': score,
        'factors': factors,
        'suggestions': ai_suggestions,
        'role': role
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
