# Document Management System Backend

A Flask-based backend system for document management with OpenAI integration.

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (for Celery)
- OpenAI API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd documents/backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` file and configure:
```
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost/dbname
OPENAI_API_KEY=your_openai_api_key
```

## Database Setup

1. Create PostgreSQL database:
```bash
createdb dbname
```

2. Initialize vector extension:
```bash
flask init-vector-extension
```

3. Run database migrations:
```bash
flask db upgrade
```

4. (Optional) Seed initial data:
```bash
flask seed run
```

## Running the Application

1. Start Redis server (for Celery):
```bash
redis-server
```

2. Start Celery worker:
```bash
celery -A app.celery worker --loglevel=info
```

3. Start Flask development server:
```bash
flask run
```

The API will be available at `http://localhost:8000`

## API Documentation

Access the API documentation at `http://localhost:8000/api/docs` when the server is running.

## Environment Variables

- `FLASK_APP`: Set to "app"
- `FLASK_ENV`: "development" or "production"
- `DATABASE_URL`: PostgreSQL connection URL
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Secret key for JWT tokens
- `REDIS_URL`: Redis connection URL for Celery

## Development

To create new database migrations:
```bash
flask db migrate -m "Migration message"
flask db upgrade
```
celery -A make_celery worker --loglevel INFO
celery -A make_celery beat --loglevel INFO
