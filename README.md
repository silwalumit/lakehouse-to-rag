# Lakehouse-to-RAG Pipeline

A complete end-to-end data pipeline that scrapes websites, processes data through a lakehouse architecture, and provides RAG (Retrieval-Augmented Generation) capabilities.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scraper   │───▶│   MinIO     │───▶│   Spark     │───▶│   Delta     │
│             │    │  (Storage)  │    │  (ETL)      │    │   Lake      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                            
┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│   RAG API   │◀───│   Chroma    │◀───│ Embeddings  │◀──────┘
│  (FastAPI)  │    │ (Vector DB) │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Features

- **Web Scraping**: Robust scraper with crawling capabilities
- **Data Lake**: MinIO-based storage with bronze/silver/gold layers
- **ETL Pipeline**: Spark-powered transformations with Delta Lake
- **Quality Monitoring**: Comprehensive data quality checks
- **Vector Search**: Chroma-based embeddings and retrieval
- **RAG API**: FastAPI service for question answering
- **Orchestration**: Airflow DAGs for pipeline automation
- **Monitoring**: Detailed logging and statistics

## 📁 Project Structure

```
lakehouse-to-rag/
├── README.md                 # This file
├── docker-compose.yaml       # Service orchestration
├── Makefile                  # Development commands
├── architecture.png          # System architecture diagram
│
├── src/                      # Source code
│   ├── scraper/             # Web scraping module
│   │   ├── scraper.py       # Main scraper class
│   │   ├── minio_utils.py   # MinIO integration
│   │   ├── __main__.py      # CLI interface
│   │   ├── requirements.txt # Dependencies
│   │   └── Dockerfile       # Container definition
│   │
│   ├── api/                 # FastAPI service
│   │   ├── main.py          # API endpoints
│   │   ├── requirements.txt # Dependencies
│   │   └── Dockerfile       # Container definition
│   │
│   ├── helpers/             # Shared utilities
│   │   ├── duckdb_queries.py # Query utilities
│   │   ├── delta_queries.py  # Delta table queries
│   │   └── requirements.txt  # Dependencies
│   │
│   └── tests/               # Test suite
│       ├── test_scraper.py  # Scraper tests
│       ├── test_etl.py      # ETL tests
│       └── test_api.py      # API tests
│
├── airflow/                  # Airflow configuration
│   └── dags/                # Pipeline DAGs
│       ├── scrape_etl_dag.py # Main ETL pipeline
│       ├── etl_utils.py      # ETL utilities
│       └── requirements.txt  # DAG dependencies
│
├── config/                   # Configuration files
│   ├── scraper/             # Scraper configurations
│   │   └── example.yaml     # Example scraper config
│   ├── etl/                 # ETL configurations
│   └── api/                 # API configurations
│
├── data/                     # Data storage
│   ├── delta/               # Delta Lake tables
│   │   ├── bronze/          # Raw data
│   │   ├── silver/          # Cleaned data
│   │   └── gold/            # Final data
│   └── lineage/             # Data lineage logs
│
└── tests/                    # Integration tests
    ├── test_pipeline.py     # End-to-end tests
    └── test_integration.py  # Service integration tests
```

## 🛠️ Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- 4GB+ RAM available

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd lakehouse-to-rag
   ```

2. **Start services**:
   ```bash
   docker compose up -d
   ```

3. **Access services**:
   - Airflow UI: http://localhost:8080 (admin/admin)
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
   - FastAPI: http://localhost:8001
   - Chroma: http://localhost:8000

### Development Setup

1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r src/scraper/requirements.txt
   pip install -r src/api/requirements.txt
   pip install -r src/helpers/requirements.txt
   ```

3. **Run tests**:
   ```bash
   make test
   ```

## 📖 Usage

### Web Scraping

**Using CLI**:
```bash
# Single page scraping
python -m scraper --url https://example.com \
  --selectors '{"title": "h1", "content": ".main"}'

# Site crawling
python -m scraper --config config/scraper/example.yaml \
  --crawl --max-pages 50 --stats
```

**Using Airflow**:
1. Set Airflow Variables for configuration
2. Trigger the `lakehouse_etl_pipeline` DAG
3. Monitor progress in Airflow UI

### Data Pipeline

The ETL pipeline processes data through three stages:

1. **Bronze**: Raw scraped data with basic cleaning
2. **Silver**: Cleaned and normalized data
3. **Gold**: Deduplicated and enriched data

### RAG API

**Query the knowledge base**:
```bash
curl -X POST "http://localhost:8001/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'
```

## 🔧 Configuration

### Scraper Configuration

The project includes comprehensive configuration examples in `sample_config/`:

**Basic Example** (`sample_config/example.yaml`):
```yaml
site_url: "https://example.com"
selectors:
  title: "h1, .title, .page-title"
  content: ".content, .main-content, .article-content"
  author: ".author, .byline"
  date: ".date, .published-date"

advanced:
  rate_limit: 1.0
  timeout: 30
  max_retries: 3
  min_content_length: 100
  respect_robots: true
  max_pages: 50
```

**Comprehensive Examples** (`sample_config/config.yaml`):
- Blog/News sites
- Documentation sites
- E-commerce pages
- Academic papers
- API documentation
- Forum/Community sites
- Portfolio sites

**Usage Examples**:
```bash
# Use basic example (Project Gutenberg)
python -m scraper --config sample_config/example.yaml --crawl

# List available examples
python -m scraper --config sample_config/config.yaml --list-examples

# Use specific Project Gutenberg example
python -m scraper --config sample_config/config.yaml --example gutenberg_classics --crawl

# Use catalog browsing
python -m scraper --config sample_config/config.yaml --example gutenberg_catalog --crawl --max-pages 10

# Use author pages
python -m scraper --config sample_config/config.yaml --example gutenberg_authors --crawl

# Create custom configuration
cp sample_config/example.yaml my_gutenberg_config.yaml
# Edit my_gutenberg_config.yaml with your preferences
python -m scraper --config my_gutenberg_config.yaml --crawl
```

**Test the Configuration**:
```bash
# Test the Project Gutenberg configuration
python src/scraper/test_config.py
```

### Airflow Variables

Set these in Airflow UI → Admin → Variables:
- `scraper_site_url`: Target website URL
- `scraper_selectors`: YAML string of CSS selectors
- `scraper_max_pages`: Maximum pages to crawl
- `scraper_crawl`: Enable/disable crawling

## 🧪 Testing

### Unit Tests
```bash
# Test scraper
python -m pytest src/tests/test_scraper.py

# Test ETL
python -m pytest src/tests/test_etl.py

# Test API
python -m pytest src/tests/test_api.py
```

### Integration Tests
```bash
# End-to-end pipeline test
python -m pytest tests/test_pipeline.py

# Service integration test
python -m pytest tests/test_integration.py
```

## 📊 Monitoring

### Data Quality

The pipeline includes comprehensive data quality checks:
- Record counts at each stage
- Content length analysis
- Missing value detection
- Duplicate identification

### Logging

- **Scraper**: Progress and error logs
- **ETL**: Transformation statistics
- **API**: Request/response logs
- **Airflow**: Task execution logs

## 🚀 Deployment

### Production Setup

1. **Environment Variables**:
   ```bash
   export MINIO_ENDPOINT=your-minio-endpoint
   export MINIO_ACCESS_KEY=your-access-key
   export MINIO_SECRET_KEY=your-secret-key
   ```

2. **Docker Compose**:
   ```bash
   docker compose -f docker-compose.prod.yaml up -d
   ```

3. **Monitoring**:
   - Set up Prometheus/Grafana for metrics
   - Configure alerting for pipeline failures
   - Monitor resource usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Include docstrings for all classes and methods
- Write tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the docs/ directory
- **Community**: Join our discussions

---

**Built with ❤️ for the data community** 