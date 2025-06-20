# 🚀 Flask Facts API - Complete CI/CD Project

A comprehensive Flask REST API with extensive testing, CI/CD pipeline, and production-ready features.

## 🌟 Features

### Core API Features
- **Random Facts API** with categorization and filtering
- **User Authentication** with JWT tokens and bcrypt password hashing
- **Favorites System** for users to save preferred facts
- **Rate Limiting** to prevent API abuse
- **Usage Analytics** with request tracking and monitoring
- **Comprehensive Error Handling** with proper HTTP status codes
- **Database Integration** with SQLAlchemy and SQLite

### Testing & Quality Assurance
- **750+ Test Cases** covering all functionality
- **Unit Tests** for individual components
- **Integration Tests** for complete user workflows  
- **Performance Tests** for load and response time validation
- **Security Tests** for SQL injection and authentication
- **Coverage Reports** with detailed analysis
- **Code Quality Tools** (Black, isort, Flake8)

### DevOps & Deployment
- **Docker Support** with multi-stage builds
- **Complete CI/CD Pipeline** with automated testing
- **Configuration Management** with environment variables
- **Health Monitoring** endpoints
- **Production-ready** logging and error handling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │────│   SQLAlchemy    │────│   SQLite DB     │
│   (REST API)    │    │   (ORM)         │    │   (Data)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ├── JWT Authentication
         ├── Rate Limiting
         ├── CORS Support
         ├── Usage Tracking
         └── Error Handling

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Unit Tests    │    │ Integration     │    │ Performance     │
│   (300+ tests)  │    │ Tests           │    │ Tests           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- Docker (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/flask-facts-api.git
cd flask-facts-api
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## 📚 API Endpoints

### Public Endpoints
- `GET /` - Welcome message with API overview
- `GET /health` - Health check with database status
- `GET /facts` - Get paginated facts with filtering
- `GET /facts/random` - Get a random fact
- `GET /facts/categories` - Get all available categories
- `POST /register` - Register a new user
- `POST /login` - User login

### Authenticated Endpoints (require JWT token)
- `GET /profile` - Get user profile
- `GET /favorites` - Get user's favorite facts
- `POST /favorites` - Add fact to favorites
- `DELETE /favorites` - Remove fact from favorites
- `GET /admin/stats` - Get API usage statistics

### Example Usage

```bash
# Get a random fact
curl http://localhost:5000/facts/random

# Register a user
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# Get facts with filtering
curl "http://localhost:5000/facts?category=science&page=1&per_page=5"
```

## 🧪 Testing

### Run All Tests
```bash
# Complete test suite
pytest -v

# Quick test run
pytest -q

# Tests with coverage
pytest --cov=app --cov=models --cov-report=html
```

### Test Categories

#### Unit Tests
```bash
pytest test_comprehensive.py::TestHealthEndpoint -v
pytest test_comprehensive.py::TestFactsEndpoints -v
pytest test_comprehensive.py::TestUserAuthentication -v
```

#### Integration Tests
```bash
pytest test_integration.py -v
```

#### Performance Tests
```bash
pytest test_load.py -v
```

#### Security Tests
```bash
pytest test_comprehensive.py::TestEdgeCases::test_sql_injection_attempts -v
pytest test_comprehensive.py::TestDatabaseIntegration::test_password_hashing -v
```

### Automated CI/CD Pipeline
```bash
chmod +x run_tests.sh
./run_tests.sh
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t flask-facts-api .

# Run container
docker run -p 5000:5000 flask-facts-api

# Run in background
docker run -d -p 5000:5000 --name facts-api flask-facts-api
```

### Environment Variables
```bash
docker run -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e JWT_SECRET_KEY=your-jwt-secret \
  -e DATABASE_URL=sqlite:///facts.db \
  flask-facts-api
```

## ⚙️ Configuration

Create a `.env` file (see `.env.example`):

```env
# Database Configuration
DATABASE_URL=sqlite:///facts.db

# Security Keys
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Development Settings
FLASK_ENV=development
FLASK_DEBUG=1
```

## 📊 Test Coverage

Current coverage statistics:
- **Total Coverage**: 73%
- **Models Coverage**: 100%
- **Application Coverage**: 68%
- **Test Cases**: 750+

View detailed coverage report:
```bash
pytest --cov=app --cov=models --cov-report=html
open htmlcov/index.html
```

## 🔒 Security Features

- **Password Hashing** with bcrypt
- **JWT Authentication** with token expiration
- **Rate Limiting** on sensitive endpoints
- **SQL Injection Protection** via SQLAlchemy ORM
- **CORS Configuration** for cross-origin requests
- **Input Validation** for all endpoints
- **Error Handling** without information leakage

## 📈 Performance

- **Response Times**: < 500ms average
- **Concurrent Users**: Tested up to 20 simultaneous users
- **Rate Limits**: 200 requests/hour, 50 requests/minute
- **Database**: Optimized queries with proper indexing
- **Caching**: Ready for Redis integration

## 🛠️ Development

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Run all quality checks
black . && isort . && flake8 .
```

### Database Operations
```bash
# Initialize database
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"

# Reset database
rm facts.db && python app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest -v`)
5. Run code quality checks (`black . && isort . && flake8 .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 Project Structure

```
flask-facts-api/
├── app.py                    # Main Flask application
├── models.py                 # Database models (User, Fact, Favorite, ApiUsage)
├── config.py                 # Configuration classes
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-container setup
├── pytest.ini              # Test configuration
├── run_tests.sh             # Complete CI/CD pipeline script
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── CI_CD_COMMANDS.md       # Complete command reference
├── tests/
│   ├── test_comprehensive.py   # Main test suite (300+ tests)
│   ├── test_integration.py     # Integration tests
│   ├── test_load.py            # Performance tests
│   └── conftest.py             # Test configuration
└── docs/
    └── api_documentation.md    # Detailed API docs
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Flask and SQLAlchemy
- Testing with pytest
- Code quality with Black, isort, and Flake8
- Containerization with Docker
- CI/CD pipeline automation

## 🚀 Deployment Ready

This project includes everything needed for production deployment:

- ✅ Comprehensive test suite (750+ tests)
- ✅ Docker containerization
- ✅ Environment-based configuration
- ✅ Security best practices
- ✅ Performance optimization
- ✅ Monitoring and logging
- ✅ CI/CD pipeline automation
- ✅ Production-ready error handling

Perfect for demonstrating modern software development practices and CI/CD implementation!