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

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Usage

### Endpoint

**POST** `/api/v1/process-cv`

Upload a PDF file to extract CV information.

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/process-cv" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/resume.pdf"
```

### Response

```json
{
  "summary": "Experienced software engineer with 5 years in full-stack development...",
  "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
  "experience_years": 5.5
}
```

### Error Responses

- **400 Bad Request**: Invalid file type, file too large, or extraction failed
- **500 Internal Server Error**: AI processing error or server error

## Postman Collection

Import `postman_collection.json` into Postman to test the API easily.

1. Open Postman
2. Click **Import**
3. Select `postman_collection.json`
4. Update the `file` parameter with your PDF file
5. Send the request

## Project Structure

```
CV-Extractor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── response.py      # Response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py # PDF text extraction
│   │   └── ai_service.py    # AI integration
│   └── routes/
│       ├── __init__.py
│       └── cv.py            # CV processing routes
├── requirements.txt
├── .env.example
├── postman_collection.json
└── README.md
```

## Extending the Application

### Add a New AI Provider

1. Add provider configuration in `app/config.py`
2. Implement provider method in `app/services/ai_service.py`
3. Update `_validate_config()` and `summarize_cv()` methods

### Add New Extraction Fields

1. Update `CVSummaryResponse` model in `app/models/response.py`
2. Modify the AI prompt in `app/services/ai_service.py`
3. Update response parsing logic

### Support Additional File Formats

1. Add format handler in `app/services/pdf_extractor.py`
2. Update `ALLOWED_EXTENSIONS` in `app/config.py`
3. Add validation in route handler

## Testing

Test the API using:
- **cURL**: See example above
- **Postman**: Import `postman_collection.json`
- **Swagger UI**: Visit http://localhost:8000/docs
- **Python requests**:
  ```python
  import requests
  
  url = "http://localhost:8000/api/v1/process-cv"
  files = {'file': open('resume.pdf', 'rb')}
  response = requests.post(url, files=files)
  print(response.json())
  ```

## License

MIT

