# Bear Systems - Applicant Tracking System (ATS)

An intelligent, AI-powered Applicant Tracking System designed for HR consultancy and recruitment operations. This system leverages advanced machine learning models, natural language processing, and vector databases to streamline resume screening and candidate evaluation.

## 🚀 Features

- **AI-Powered Resume Screening**: Multi-provider AI support (OpenAI, Anthropic, Ollama)
- **Document Processing**: Support for PDF, DOCX, and image-based resumes with OCR
- **RAG System**: Semantic search using FAISS vector database and sentence transformers
- **Legal Compliance**: Built-in HR legal document processing and guidance
- **Payment Integration**: Razorpay payment gateway integration
- **Real-time Updates**: WebSocket support with Flask-SocketIO
- **Persistent Storage**: Supabase integration for data management
- **Advanced Analytics**: Sales intelligence and credit management systems
- **Multi-version Architecture**: Multiple iterations showcasing system evolution

## 📁 Project Structure

```
ATS/
├── Formalization/          # Initial version
├── Formalizationv2/        # Version 2
├── FormalizationV3/        # Version 3 (with advanced AI features)
├── formalizationv4/        # Version 4 (latest backend)
├── Frontend/               # Initial frontend
├── FrontendV2/             # Frontend version 2
├── v3frontend/             # Frontend version 3
├── v4frontend/             # Frontend version 4
├── v5backend/              # Backend version 5
└── v5frontend/             # Frontend version 5
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 3.0.3
- **Server**: Gunicorn with Eventlet
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: 
  - OpenAI GPT models
  - Anthropic Claude
  - Ollama (local models)
  - FAISS for vector search
  - Sentence Transformers
  - PyTorch
- **Document Processing**: 
  - PyMuPDF
  - PyPDF2
  - python-docx
  - Tesseract OCR
- **Payment**: Razorpay

### Frontend
- **Framework**: React (various versions)
- **Build Tools**: Modern JavaScript toolchain

### Infrastructure
- **Containerization**: Docker
- **Deployment**: Railway, Vercel
- **Web Server**: Nginx
- **Orchestration**: Docker Compose

## 🔧 Setup Instructions

### Prerequisites
- Python 3.11.x
- Node.js 18.x
- Docker (optional)
- Tesseract OCR

### Backend Setup

1. Navigate to the desired backend version (e.g., `FormalizationV3`):
```bash
cd FormalizationV3
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with required credentials:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
SECRET_KEY=your_secret_key
```

5. Run the application:
```bash
python app.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd v5frontend  # or your preferred frontend version
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## 🐳 Docker Deployment

Run with Docker Compose:
```bash
docker-compose up -d
```

## 📋 Key Features by Version

### FormalizationV3
- Multi-provider AI integration
- Advanced RAG system with FAISS
- HR legal document processing
- Credit management system
- Payment integration

### formalizationv4
- Enhanced CORS configuration
- Improved authentication middleware
- Advanced logging and debugging
- Refined deployment strategies

### v5backend/frontend
- Latest architectural improvements
- Optimized performance
- Enhanced security features

## 🔒 Security

- API keys and secrets are encrypted and stored securely
- Environment variables for sensitive data
- Authentication middleware for protected routes
- Rate limiting on API endpoints
- CORS configuration for cross-origin requests

## 📝 Documentation

Additional documentation is available in:
- [Deployment Guide](formalizationv4/DEPLOYMENT_GUIDE.md)
- [Railway Deployment](Formalization/railway-deploy.md)
- [Application Architecture](FormalizationV3/APPLICATION_ARCHITECTURE_ANALYSIS.md)
- [Refactoring Guide](FormalizationV3/REFACTORING_GUIDE.md)

## 🚀 Deployment

The application supports multiple deployment platforms:
- **Railway**: Automated deployment with `railway.toml`
- **Vercel**: Frontend deployment
- **Docker**: Containerized deployment
- **Traditional**: VPS deployment with Nginx

## 📊 System Capabilities

- Resume parsing and extraction
- Semantic candidate matching
- Automated screening workflows
- Credit-based system for API usage
- Payment processing and subscriptions
- Real-time notifications
- Advanced analytics and reporting
- Legal compliance checking

## 🤝 Contributing

This is a private HR consultancy system. For inquiries about contributions or collaboration, please contact the development team.

## 📄 License

Proprietary - Bear Systems. All rights reserved.

## 🔗 Contact

For support or inquiries, please contact the Bear Systems team.

---

**Note**: This system contains multiple versions representing the evolution of the platform. Each version contains improvements and refinements over previous iterations. For production use, refer to the latest stable version (v5backend/v5frontend or formalizationv4).
# ATS
