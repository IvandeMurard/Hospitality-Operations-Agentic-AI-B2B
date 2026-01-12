FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Environment: disable file logging by default in production
ENV DISABLE_FILE_LOGGING=true

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Start FastAPI (module path: backend.main:app)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
