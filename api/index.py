import os
import sys
from flask import Flask, render_template, request, jsonify
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import google.generativeai as genai
import PyPDF2
from docx import Document
import re
from datetime import datetime
import json
import tempfile

# Create Flask app
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-this')

# Configure Gemini API
try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        model = None
except Exception as e:
    model = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_content):
    try:
        reader = PyPDF2.PdfReader(file_content)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_content):
    try:
        doc = Document(file_content)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_txt(file_content):
    try:
        return file_content.read().decode('utf-8')
    except Exception as e:
        return f"Error reading TXT: {str(e)}"

def calculate_ats_score(resume_text, role="general"):
    score = 0
    factors = {}
    
    # Contact Information (20 points)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+?\d{1,3}[-.\ s]?)?\(?\d{3}\)?[-.\ s]?\d{3}[-.\ s]?\d{4}'
    
    if re.search(email_pattern, resume_text):
        score += 10
        factors['Email'] = 10
    else:
        factors['Email'] = 0
        
    if re.search(phone_pattern, resume_text):
        score += 10
        factors['Phone'] = 10
    else:
        factors['Phone'] = 0
    
    # Professional Sections (40 points total)
    sections = ['experience', 'education', 'skills', 'summary', 'objective']
    section_score = 0
    for section in sections:
        if re.search(rf'\b{section}\b', resume_text, re.IGNORECASE):
            section_score += 8
    factors['Professional Sections'] = min(section_score, 40)
    score += factors['Professional Sections']
    
    # Keywords (25 points)
    keywords = ['project', 'manage', 'develop', 'create', 'implement', 'analyze', 'design', 'lead', 'coordinate']
    keyword_count = sum(1 for keyword in keywords if keyword.lower() in resume_text.lower())
    factors['Keywords'] = min(keyword_count * 3, 25)
    score += factors['Keywords']
    
    # Quantifiable Achievements (15 points)
    number_pattern = r'\b\d+%|\b\d+\s*(years?|months?|weeks?|days?)\b|\$\d+|\b\d+\+?\b'
    numbers = re.findall(number_pattern, resume_text)
    factors['Quantifiable Achievements'] = min(len(numbers) * 2, 15)
    score += factors['Quantifiable Achievements']
    
    return min(score, 100), factors

def get_ai_suggestions(resume_text, score, factors):
    if not model:
        return "AI suggestions unavailable - Gemini API key not configured"
    
    try:
        prompt = f"""
        Analyze this resume and provide specific improvement suggestions:
        
        Resume Text: {resume_text[:2000]}...
        Current ATS Score: {score}/100
        
        Provide suggestions in these categories:
        1. Priority Actions (high impact improvements)
        2. Content Suggestions (what to add/modify)
        3. Formatting Tips (structure improvements)
        4. Keyword Enhancements (industry-specific terms)
        
        Format as JSON with categories as keys and arrays of suggestions as values.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI analysis unavailable: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        role = request.form.get('role', 'general')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT files.'}), 400
        
        # Extract text based on file type
        filename = file.filename.lower()
        if filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file)
        elif filename.endswith('.docx'):
            resume_text = extract_text_from_docx(file)
        elif filename.endswith('.txt'):
            resume_text = extract_text_from_txt(file)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        if resume_text.startswith('Error'):
            return jsonify({'error': resume_text}), 400
        
        # Calculate ATS score
        score, factors = calculate_ats_score(resume_text, role)
        
        # Get AI suggestions
        suggestions = get_ai_suggestions(resume_text, score, factors)
        
        return jsonify({
            'score': score,
            'factors': factors,
            'suggestions': suggestions,
            'role': role
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        role = data.get('role', 'general')
        
        if not resume_text.strip():
            return jsonify({'error': 'Please provide resume text'}), 400
        
        # Calculate ATS score
        score, factors = calculate_ats_score(resume_text, role)
        
        # Get AI suggestions
        suggestions = get_ai_suggestions(resume_text, score, factors)
        
        return jsonify({
            'score': score,
            'factors': factors,
            'suggestions': suggestions,
            'role': role
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
