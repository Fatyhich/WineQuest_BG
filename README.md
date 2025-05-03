# Image and Text Processing Service

A web service that processes images and text using background workers.

## Features

- REST API for submitting images and text for processing
- Background workers for handling long-running tasks
- Job status tracking
- Scalable architecture with Redis message queue

## Architecture

- **Flask**: Web framework for the REST API
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker and result backend
- **Docker**: Containerization for easy deployment

## Setup and Installation

### Using Docker Compose (Recommended)

1. Clone the repository
2. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
3. Customize the `.env` file if needed
4. Build and start the services:
   ```
   docker-compose up -d
   ```

### Manual Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Install and start Redis
5. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```
6. Start the Flask API:
   ```
   gunicorn app:app
   ```
7. Start Celery workers:
   ```
   celery -A celery_worker.celery_app worker --loglevel=info
   ```

## API Endpoints

### Submit Image and Text for Processing

```
POST /api/process
```

**Parameters:**
- `image`: Image file (form-data)
- `text`: Text string (form-data)

**Response:**
```json
{
  "job_id": "unique-job-id",
  "status": "processing"
}
```

### Check Job Status

```
GET /api/status/<job_id>
```

**Response:**
```json
{
  "status": "pending|processing|completed|failed",
  "message": "Status message",
  "result": { /* Results if completed */ }
}
```

## Configuration

The service can be configured using environment variables:

- `DEBUG`: Enable debug mode (default: False)
- `SECRET_KEY`: Flask secret key
- `CELERY_BROKER_URL`: Redis URL for Celery broker
- `CELERY_RESULT_BACKEND`: Redis URL for Celery results
- `WORKER_COUNT`: Number of Celery workers to run (default: 2)
- `UPLOAD_FOLDER`: Path to store uploaded images

## Scaling Workers

You can scale the number of workers by setting the `WORKER_COUNT` environment variable:

```
WORKER_COUNT=4 docker-compose up -d --scale worker=4
```