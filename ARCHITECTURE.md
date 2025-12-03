# Architecture Note

This API follows a service-oriented architecture with clear separation of concerns: **Routes** handle HTTP requests/responses, **Services** contain business logic (PDF extraction via pdfplumber/PyPDF2 and AI integration with OpenAI/Gemini), and **Models** define data schemas. The modular design allows easy extension to new AI providers or file formats without modifying core functionality.

