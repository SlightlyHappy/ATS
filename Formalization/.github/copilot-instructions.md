# Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a full-stack resume screening application project with the following structure:

## Project Structure
- `frontend/` - React application for file upload and dashboard
- `backend/` - Python Flask API for resume processing and analysis
- `sample_resumes/` - Test files for development

## Key Technologies
- Frontend: React, Chart.js for visualizations, Axios for API calls
- Backend: Flask, pytesseract/EasyOCR for OCR, python-docx for DOCX parsing, Ollama for LLM integration
- File Processing: Support for PDF, DOCX, and image files
- AI Integration: Local Ollama LLM for resume scoring and feedback

## Development Guidelines
- Use functional components with React hooks
- Implement proper error handling for file uploads and processing
- Follow REST API conventions for backend endpoints
- Use environment variables for configuration
- Ensure offline functionality with no external API dependencies
- Implement CORS for local development between frontend (port 3000) and backend (port 8000)

## Features to Implement
- Multi-file upload with progress tracking
- OCR text extraction from PDFs and images
- Resume parsing for key information (name, skills, experience, education)
- AI-powered scoring and feedback using local Ollama
- Dashboard with charts and tables
- Filtering, sorting, and CSV export functionality
