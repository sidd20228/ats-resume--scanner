# ATS Resume Scanner

An intelligent ATS (Applicant Tracking System) resume scanner that provides scoring and AI-based suggestions using Google's Gemini 1.5 API.

## Features

- **Resume Upload**: Support for PDF, DOCX, and TXT files
- **Text Analysis**: Direct text input for quick analysis
- **ATS Scoring**: Comprehensive scoring algorithm (0-100)
- **AI Suggestions**: Powered by Gemini 1.5 API for personalized recommendations
- **Modern UI**: Beautiful, responsive web interface
- **Real-time Analysis**: Instant feedback and suggestions

## Scoring Criteria

The ATS scanner evaluates resumes based on:

1. **Contact Information (20 points)**
   - Email address presence (10 points)
   - Phone number presence (10 points)

2. **Professional Sections (40 points)**
   - Experience, Education, Skills, Summary/Objective sections
   - Up to 8 points per section found

3. **Keywords & Technical Terms (25 points)**
   - Common professional keywords
   - Industry-relevant terminology

4. **Quantifiable Achievements (15 points)**
   - Numbers, percentages, metrics
   - Measurable accomplishments

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ats-resume-scanner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

4. **Get Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key to your `.env` file

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **Upload or paste resume**
   - Upload PDF, DOCX, or TXT files
   - Or paste resume text directly

4. **Get instant analysis**
   - ATS compatibility score
   - Detailed factor breakdown
   - AI-powered improvement suggestions

## API Endpoints

- `GET /` - Main application interface
- `POST /upload` - Upload resume file for analysis
- `POST /analyze` - Analyze resume text directly

## File Structure

```
ats-resume-scanner/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # Project documentation
├── templates/
│   └── index.html        # Main web interface
└── uploads/              # Temporary file storage (auto-created)
```

## Technologies Used

- **Backend**: Flask (Python)
- **AI**: Google Gemini 1.5 API
- **File Processing**: PyPDF2, python-docx
- **Frontend**: Bootstrap 5, Font Awesome
- **Styling**: Modern CSS with gradients and animations

## Security Features

- File type validation
- Secure filename handling
- Temporary file cleanup
- File size limits (16MB max)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please create an issue in the repository or contact me.
