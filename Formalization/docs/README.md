# 🎯 Resume Screening Application

A comprehensive full-stack application for automated resume screening and2. **Start Backend Server** (Port 8000)
   ```bash
   cd backend
   # Activate virtual environment first
   python app.py
   ```

3. **Start Frontend Server** (Port 3000)
   ```bash
   cd frontend
   npm start
   ```

4. **Access the Application**
   - Open your browser and go to: `http://localhost:3000`
   - Backend API available at: `http://localhost:8000`
   - Configure AI provider in the "AI Settings" tab before uploading resumesAI. Built with React frontend and Python Flask backend, featuring OCR text extraction and local LLM integration for completely offline processing.

## ✨ Features

### Frontend (React)
- 📁 **Multi-file Upload**: Drag & drop interface for multiple resume files
- 📊 **Interactive Dashboard**: Real-time analytics with charts and tables
- 🔍 **Smart Filtering**: Search and sort candidates by various criteria
- 📈 **Data Visualization**: Score distribution and skills analysis charts
- 💾 **CSV Export**: Export analysis results for further processing
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices

### Backend (Python Flask)
- 🔍 **OCR Processing**: Extract text from PDFs and images using pytesseract
- 📄 **Document Parsing**: Handle DOCX files with python-docx
- 🤖 **AI Analysis**: Local LLM integration with Ollama for resume scoring
- 🏷️ **Information Extraction**: Parse names, skills, experience, and education
- 🔒 **Privacy First**: 100% offline processing - no external API calls
- ⚡ **RESTful API**: Clean API endpoints with proper error handling

### AI Integration
- 🧠 **Multi-Provider AI**: Choose between Ollama (local), OpenAI, or Google Gemini
- 🔧 **Flexible Configuration**: Easy AI provider switching with API key management
- 📊 **Scoring System**: Comprehensive scoring (overall, technical, experience, education)
- 💡 **Feedback Generation**: Strengths, weaknesses, and recommendations
- 🎯 **Resume Ranking**: Automatic candidate ranking and comparison
- 🔒 **Privacy Options**: Local processing with Ollama or cloud-based analysis

## 🚀 Quick Start

### Prerequisites

1. **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
2. **Python** (v3.8 or higher) - [Download](https://python.org/)
3. **AI Provider** (choose one):
   - **Ollama** - [Install Ollama](https://ollama.ai/) for local processing
   - **OpenAI API** - [Get API Key](https://platform.openai.com/api-keys)
   - **Google Gemini** - [Get API Key](https://makersuite.google.com/app/apikey)
4. **Tesseract OCR** - Required for image text extraction

#### Install Tesseract OCR:

**Windows:**
```powershell
# Using Chocolatey
choco install tesseract

# Or download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Installation Steps

1. **Clone or setup the project**
   ```bash
   cd "d:\Documents V2.1\Coding\HR Consultancy\ATS\Formalization"
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Setup AI Provider (Optional for Ollama)**
   ```bash
   # Only if using Ollama - Install Ollama (follow instructions at https://ollama.ai/)
   
   # Pull your preferred model
   ollama pull llama3
   # or
   ollama pull qwen2.5:7b
   
   # Start Ollama service
   ollama serve
   ```

### 🏃‍♂️ Running the Application

1. **Configure AI Provider**
   - Open the application and go to "AI Settings" tab
   - Choose your AI provider (Ollama, OpenAI, or Gemini)
   - For OpenAI/Gemini: Enter your API key
   - Test the connection and save settings

2. **Start Backend Server** (Port 8000)
   ```bash
   cd backend
   # Activate virtual environment first
   python app.py
   ```

2. **Start Frontend Server** (Port 3000)
   ```bash
   cd frontend
   npm start
   ```

3. **Access the Application**
   - Open your browser and go to: `http://localhost:3000`
   - Backend API available at: `http://localhost:8000`

## 📁 Project Structure

```
Formalization/
├── frontend/                    # React frontend application
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.js   # File upload component
│   │   │   └── Dashboard.js    # Analytics dashboard
│   │   ├── App.js              # Main application component
│   │   ├── App.css             # Styling
│   │   └── index.js            # React entry point
│   ├── package.json
│   └── ...
├── backend/                     # Python Flask backend
│   ├── app.py                  # Main Flask application
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment configuration
│   └── uploads/                # Temporary file storage
├── sample_resumes/             # Test resume files
│   ├── john_smith_resume.txt
│   ├── sarah_johnson_resume.txt
│   └── ...
├── .github/
│   └── copilot-instructions.md
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Backend Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
```

### Frontend Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/test-ai` | Test AI provider connection |
| POST | `/api/upload` | Upload and process resume files |
| GET | `/api/resumes` | Get all processed resumes |
| GET | `/api/resumes/<id>` | Get specific resume by ID |
| GET | `/api/export` | Export results as CSV |
| DELETE | `/api/clear` | Clear all processed resumes |

## 📄 Supported File Formats

- **PDF**: Text extraction using PyMuPDF
- **DOCX**: Direct text extraction using python-docx
- **Images**: OCR using pytesseract
  - PNG, JPG, JPEG, GIF, BMP, TIFF

## 🤖 AI Analysis Features

The application supports multiple AI providers for resume analysis:

### **Local Processing (Ollama)**
- 🔒 **Privacy**: 100% offline processing
- 💸 **Cost**: Free to use
- 🖥️ **Requirements**: Local installation and GPU/CPU resources
- 📊 **Models**: Llama 3, Qwen 2.5, Mistral, Code Llama

### **Cloud Processing (OpenAI/Gemini)**
- 🚀 **Performance**: Faster and more accurate analysis
- 💳 **Cost**: Pay-per-use API pricing
- 🌐 **Requirements**: Internet connection and API key
- 🧠 **Models**: GPT-4o, GPT-3.5, Gemini Pro, Gemini Flash

### **Analysis Output**
All providers generate:
- **Overall Score** (1-100): Comprehensive resume evaluation
- **Technical Skills Score**: Programming languages, frameworks, tools
- **Experience Score**: Years of experience, roles, responsibilities
- **Education Score**: Degrees, certifications, institutions
- **Role Fit Score**: Match against job requirements
- **Strengths**: Key positive aspects of the candidate
- **Weaknesses**: Areas for improvement
- **Recommendations**: Hiring decisions and interview focus areas

## 🔍 Extracted Information

The system automatically extracts:

- **Personal Information**: Name, email, phone number
- **Skills**: Programming languages, technologies, frameworks
- **Experience**: Years of experience, companies worked for
- **Education**: Degrees, universities, certifications
- **Text Statistics**: Character count, processing metadata

## 🛠️ Troubleshooting

### Common Issues

1. **AI Provider Connection Error**
   - **Ollama**: Ensure Ollama is running: `ollama serve`
   - **Ollama**: Check if model is installed: `ollama list`
   - **OpenAI**: Verify API key is valid and has credits
   - **Gemini**: Ensure API key is correct and service is accessible
   - **All**: Test connection in AI Settings tab

2. **AI Analysis Fails**
   - Check AI provider settings and test connection
   - Verify API key permissions and quotas
   - For Ollama: Ensure sufficient system resources
   - Review error messages in Debug Console

3. **OCR Not Working**
   - Install Tesseract OCR on your system
   - Verify Tesseract is in your PATH
   - Check image quality and format

4. **File Upload Issues**
   - Ensure AI provider is configured first
   - Check file size limits (16MB default)
   - Verify file format is supported
   - Ensure backend server is running

4. **CORS Errors**
   - Verify backend server is running on port 8000
   - Check frontend proxy configuration
   - Ensure Flask-CORS is properly configured

### Development Tips

- Use browser developer tools to debug frontend issues
- Check backend console for error messages
- Monitor network requests in browser dev tools
- Verify API responses using tools like Postman

## 🔒 Privacy & Security

- **100% Offline Processing**: No data sent to external servers
- **Local AI**: Uses locally hosted Ollama LLM
- **Temporary Storage**: Uploaded files are deleted after processing
- **No Data Persistence**: Resume data stored in memory only
- **CORS Protection**: Configured for local development

## 🚀 Production Deployment

For production deployment:

1. **Backend**:
   - Use production WSGI server (Gunicorn, uWSGI)
   - Configure proper logging
   - Set up database for persistent storage
   - Implement authentication if needed

2. **Frontend**:
   - Build optimized production bundle: `npm run build`
   - Serve static files with nginx or similar
   - Configure proper environment variables

3. **AI Service**:
   - Deploy Ollama on dedicated server
   - Consider GPU acceleration for better performance
   - Monitor resource usage and scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the GitHub issues
3. Create a new issue with detailed information
4. Include error messages and system information

## 🎯 Future Enhancements

- [ ] Database integration for persistent storage
- [ ] User authentication and authorization
- [ ] Batch processing for large volumes
- [ ] Integration with ATS systems
- [ ] Custom scoring criteria configuration
- [ ] Resume template analysis
- [ ] Advanced NLP for better information extraction
- [ ] Multi-language support
- [ ] Interview scheduling integration

---

**Built with ❤️ using React, Flask, and Ollama**
#   R e s u m e S c r e a n i n g A P P 
 
 