# Perplexity Research Prompt for Python 3.11 Compatible Requirements

## Research Query for Perplexity:

```
I need to create a compatible requirements.txt file for a Flask application running on Python 3.11 slim (Docker environment) with the following specific requirements and constraints:

**Environment Details:**
- Python 3.11.13 (slim Docker image)
- Flask application with AI-powered resume analysis
- Deployment target: Railway cloud platform
- Need OCR capabilities (EasyOCR + PyTorch ecosystem)
- Current error: "operator torchvision::nms does not exist"

**Core Dependencies That Must Work Together:**
1. **Flask Ecosystem:**
   - Flask==3.1.1
   - Flask-SQLAlchemy==3.1.0
   - Flask-SocketIO==5.3.6

2. **AI/ML Stack (CRITICAL - currently failing):**
   - easyocr (for OCR text extraction)
   - torch (PyTorch)
   - torchvision (computer vision)
   - sentence-transformers==2.2.2
   - chromadb==0.4.15
   - langchain==0.1.17

3. **Document Processing:**
   - PyPDF2==3.0.1
   - python-docx==1.1.2
   - pdfplumber==0.11.4
   - PyMuPDF==1.25.1
   - numpy, pandas, Pillow

4. **Database & Production:**
   - psycopg2-binary==2.9.10
   - SQLAlchemy==2.0.21
   - gunicorn==23.0.0

**Specific Research Questions:**

1. **What are the exact compatible versions of torch, torchvision, and easyocr that work together on Python 3.11 in 2025?** Include version combinations that avoid the "operator torchvision::nms does not exist" error.

2. **Which torch index URL should be used for CPU-only PyTorch installation on Python 3.11?** (e.g., --index-url https://download.pytorch.org/whl/cpu)

3. **Are there any known compatibility issues between sentence-transformers 2.2.2 and the latest torch/torchvision versions?**

4. **What's the recommended installation order for PyTorch ecosystem packages to avoid dependency conflicts?**

5. **For Python 3.11 slim Docker images, which system packages are required for:**
   - EasyOCR compilation
   - OpenCV dependencies
   - PyTorch CPU backend

6. **Are there alternative OCR libraries that are more stable than EasyOCR for production deployment?** (e.g., PaddleOCR, TrOCR)

7. **What are the production-tested version combinations for:**
   - torch + torchvision + transformers + sentence-transformers
   - That specifically work on Railway/similar cloud platforms

**Additional Context:**
- Application successfully deploys when torch/easyocr are commented out
- Ollama runs successfully (qwen2.5:7b model)
- SQLAlchemy and Flask layers work fine
- Only the torchvision import causes the crash

Please provide specific version numbers, installation commands, and any Docker/system-level dependencies needed for a stable production deployment.
```

## Follow-up Research Questions:

After getting the initial response, ask these follow-up questions:

```
Based on your previous response, please provide:

1. **A complete requirements.txt section** with exact version numbers for the PyTorch ecosystem that you verified work together on Python 3.11

2. **Docker installation commands** - what apt packages need to be installed in python:3.11-slim for the recommended versions?

3. **pip install order** - should torch be installed first, or is there a specific sequence?

4. **Environment variables or configurations** needed for CPU-only torch in production?

5. **Alternative solutions** - if EasyOCR remains problematic, what are the best production-ready OCR alternatives that integrate well with the rest of the stack?
```

## How to Use This Research:

1. Copy the first research query and paste it into Perplexity
2. Review the response and note the specific version numbers
3. Use the follow-up questions to get more detailed implementation guidance
4. Test the recommended versions in a development environment first
5. Update requirements.txt with the verified compatible versions

## Expected Outcome:

A requirements.txt file with proven compatible versions that will allow your Flask application to start successfully with all AI/ML capabilities enabled.
