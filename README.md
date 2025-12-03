# CV Extractor API

A clean, extensible REST API for extracting and summarizing CV/resume information from PDF files using AI (OpenAI or Google Gemini).

## Features

- 📄 PDF text extraction
- 🤖 AI-powered CV summarization (OpenAI GPT or Google Gemini)
- 📊 Structured JSON response (summary, skills, experience years)
- 🏗️ Clean, modular architecture
- ✅ Comprehensive error handling
- 📝 Auto-generated API documentation

## Architecture

**Clean Separation of Concerns:**
- **Routes** (`app/routes/`): Handle HTTP requests/responses
- **Services** (`app/services/`): Business logic (PDF extraction, AI integration)
- **Models** (`app/models/`): Data schemas and validation
- **Config** (`app/config.py`): Centralized configuration management

The application follows a service-oriented architecture where each component has a single responsibility, making it easy to extend (e.g., add new AI providers, support different file formats, or add new extraction fields).

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
AI_PROVIDER=openai  # or "gemini"
OPENAI_API_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### cURL Example

**Windows Command Prompt:**
```cmd
curl.exe --noproxy "*" -X POST "http://127.0.0.1:8000/api/v1/process-cv" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@Senior Full Stack & AI Engineer.pdf;type=application/pdf"
```

**If file is in a different location (use full path like below):**
```cmd
curl.exe --noproxy "*" -X POST "http://127.0.0.1:8000/api/v1/process-cv" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@C:\Users\Administrator\Music\openAI-CV-Extractor\Senior Full Stack & AI Engineer.pdf;type=application/pdf"
```

**Linux/Mac:**
```bash
curl -X POST "http://localhost:8000/api/v1/process-cv" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/resume.pdf;type=application/pdf"
```

### Postman Example

Import `postman_collection.json` into Postman to test the API easily.

1. Open Postman
2. Click **Import**
3. Select `postman_collection.json`
4. Update the `file` parameter with your PDF file
5. Send the request

## License

MIT

