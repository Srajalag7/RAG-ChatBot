# GitLab ChatBot

A FastAPI-based chatbot that scrapes GitLab Handbook and Direction pages, creates embeddings, and provides intelligent responses using Google Gemini AI.

## Features

- **Web Scraping**: Recursively scrapes GitLab Handbook and Direction pages
- **Vector Embeddings**: Uses Google Gemini embeddings for semantic search
- **Multi-Query Processing**: Intelligently splits complex queries into multiple sub-queries
- **Chat Interface**: RESTful API for chat conversations
- **Database Storage**: PostgreSQL with Supabase for data persistence
- **Vector Search**: pgvector for similarity search

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Supabase account
- Google Gemini API key

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd GitLab-ChatBot

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon key
- `GEMINI_API_KEY`: Your Google Gemini API key

### 4. Database Setup

1. Create a new Supabase project
2. Run the SQL schemas in your Supabase SQL editor:
   - `database_schema.sql` - Main database tables
   - `embeddings_schema.sql` - Vector embeddings support

### 5. Run the Application

```bash
# Start the API server
python run.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```
Check API health status and database connectivity

### Root
```
GET /
```
Get API information and version

### Scraping
```
GET /scraper/sites
```
Get all available sites from configuration

```
POST /scraper/scrape
```
Scrape a site and store all discovered URLs

### Embeddings
```
POST /embeddings/generate
```
Generate embeddings for all content in the database

### Chat Management
```
POST /chats/
```
Create a new chat session

```
GET /chats/
```
Get all chat sessions with pagination

```
GET /chats/{chat_id}
```
Get a specific chat with its conversations

```
POST /chats/{chat_id}/messages
```
Send a message in a chat and get bot response

```
DELETE /chats/{chat_id}
```
Delete a chat and all its conversations

### Multi-Query Processing
```
POST /multi-query/process
```
Process a user query through the multi-query pipeline

## Configuration

All configuration options in `.env`:

### Scraper Configuration
- `MAX_DEPTH`: Maximum depth for recursive URL scraping (default: 3)
- `MAX_CONTENT_LENGTH`: Maximum content length to save per page in characters (default: 100000)
- `SITES_CONFIG`: JSON configuration for sites to scrape
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `REQUEST_DELAY`: Delay between requests in seconds (default: 1)

### API Configuration
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)

### Performance Configuration
- `API_DELAY`: Delay between API requests in seconds (default: 1.0)
- `MAX_RETRIES`: Maximum number of retries for failed requests (default: 3)
- `RETRY_DELAY`: Base delay for exponential backoff in seconds (default: 2.0)
- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent API requests (default: 1)

### Supabase Database Configuration
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon key
- `SAVE_TO_DATABASE`: Whether to save data to database (default: true)

### Gemini AI Configuration
- `GEMINI_API_KEY`: Your Google Gemini API key
- `GEMINI_EMBEDDING_MODEL`: Gemini model name for embeddings (default: gemini-embedding-001)
- `GEMINI_EMBEDDING_DIMENSIONS`: Gemini embedding dimensions (default: 1536)

### Embedding Configuration
- `CHUNK_SIZE`: Text chunking size (default: 4000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 400)

### LLM Configuration for Query Analysis
- `QUERY_ANALYSIS_MODEL`: Model for query analysis and splitting (default: gemini-2.5-flash)
- `QUERY_ANALYSIS_TEMPERATURE`: Temperature for query analysis (default: 0.1)
- `QUERY_ANALYSIS_MAX_TOKENS`: Maximum tokens for query analysis response (default: 2048)

### LLM Configuration for Final Response
- `RESPONSE_MODEL`: Model for final response generation (default: gemini-2.5-flash)
- `RESPONSE_TEMPERATURE`: Temperature for response generation (default: 0.2)
- `RESPONSE_MAX_TOKENS`: Maximum tokens for response generation (default: 4096)

### Document Retrieval Configuration
- `DOCUMENTS_PER_QUERY`: Number of documents to retrieve per query (default: 5)
- `MAX_TOTAL_DOCUMENTS`: Maximum total documents to return after reranking (default: 15)

## Project Structure

```
GitLab-ChatBot/
├── app/                                 # Main application package
│   ├── __init__.py                      # Package initialization
│   ├── main.py                          # FastAPI application entry point
│   ├── config/                          # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py                  # Environment settings and configuration
│   ├── controllers/                     # API route handlers
│   │   ├── __init__.py
│   │   ├── chat_controller.py           # Chat and conversation endpoints
│   │   ├── embedding_controller.py      # Embedding generation endpoints
│   │   ├── multi_query_controller.py    # Multi-query processing endpoints
│   │   └── scraper_controller.py        # Web scraping endpoints
│   ├── models/                          # Database models and schemas
│   │   ├── __init__.py
│   │   ├── database.py                  # Database connection and models
│   │   └── schemas.py                   # Pydantic schemas for API
│   └── services/                        # Business logic services
│       ├── __init__.py
│       ├── chat_service.py              # Chat management logic
│       ├── database_service.py          # Database operations
│       ├── embedding_service.py         # Embedding generation logic
│       ├── multi_query_flow_service.py  # Multi-query processing flow
│       ├── query_analysis_service.py    # Query analysis and splitting
│       ├── response_service.py          # Response generation logic
│       ├── retrieval_service.py         # Document retrieval logic
│       └── scraper_service.py           # Web scraping logic
├── prompts/                             # AI prompts and templates
│   ├── __init__.py
│   └── multi_query_prompt.py            # Multi-query processing prompts
├── database_schema.sql                  # Main database schema for Supabase
├── embeddings_schema.sql                # Vector embeddings schema with pgvector
├── env.example                          # Environment variables template
├── requirements.txt                     # Python dependencies
├── run.py                               # Application runner script
├── .gitignore                           # Git ignore rules
└── README.md                            # Project documentation
```

## Technologies Used

- **FastAPI**: Web framework
- **Supabase**: Database and authentication
- **Google Gemini**: AI embeddings and chat
- **pgvector**: Vector similarity search
- **BeautifulSoup**: Web scraping
- **LangChain**: AI framework
- **SQLAlchemy**: ORM

## License

[Add your license here]
