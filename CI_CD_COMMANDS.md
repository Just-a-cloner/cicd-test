# Complete CI/CD Pipeline Commands

## Step-by-Step Development to Production Commands

### 🔧 **Step 1: Environment Setup**
```bash
# Check versions
python --version
pip --version

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 📦 **Step 2: Install Dependencies**
```bash
# Install project dependencies
pip install -r requirements.txt

# Install development dependencies
pip install flake8 black isort pytest-cov
```

### 🔍 **Step 3: Code Quality & Linting**
```bash
# Code formatting (auto-fix)
black .

# Import sorting (auto-fix) 
isort .

# Code formatting check (CI mode)
black --check --diff .

# Import sorting check (CI mode)
isort --check-only --diff .

# Linting for critical errors
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Full linting
flake8 .
```

### 🧪 **Step 4: Testing Commands**

#### Unit Tests
```bash
# Run all unit tests
pytest test_comprehensive.py::TestHealthEndpoint -v
pytest test_comprehensive.py::TestFactsEndpoints -v
pytest test_comprehensive.py::TestUserAuthentication -v
pytest test_comprehensive.py::TestDatabaseIntegration -v

# Run specific test
pytest test_comprehensive.py::TestHealthEndpoint::test_health_check_success -v
```

#### Integration Tests
```bash
# Run integration tests
pytest test_integration.py -v

# Run specific integration test
pytest test_integration.py::TestIntegrationScenarios::test_complete_user_journey -v
```

#### Performance Tests
```bash
# Run performance tests
pytest test_load.py -v

# Run specific performance test
pytest test_load.py::TestLoadAndPerformance::test_response_time_benchmarks -v
```

#### All Tests
```bash
# Run all tests (comprehensive)
pytest -v

# Run tests quietly
pytest -q

# Run tests with short traceback
pytest --tb=short
```

### 📊 **Step 5: Test Coverage**
```bash
# Generate coverage report
pytest --cov=app --cov=models --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov=models --cov-report=html

# View HTML coverage
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

### 🔒 **Step 6: Security Testing**
```bash
# Run security-focused tests
pytest test_comprehensive.py::TestEdgeCases::test_sql_injection_attempts -v
pytest test_comprehensive.py::TestDatabaseIntegration::test_password_hashing -v

# Run edge case tests
pytest test_comprehensive.py::TestEdgeCases -v
```

### 🚀 **Step 7: Application Commands**

#### Local Development
```bash
# Run application in development mode
python app.py

# Run with specific host/port
flask run --host=0.0.0.0 --port=5000

# Run in debug mode
FLASK_DEBUG=1 python app.py
```

#### Production-like Testing
```bash
# Test application startup
timeout 10s python app.py &

# Quick endpoint tests
curl http://localhost:5000/health
curl http://localhost:5000/facts
curl http://localhost:5000/facts/random
```

### 🐳 **Step 8: Docker Commands**

#### Build
```bash
# Build Docker image
docker build -t cicd-test-app .

# Build with tag
docker build -t cicd-test-app:v1.0 .
```

#### Run
```bash
# Run container
docker run -p 5000:5000 cicd-test-app

# Run in background
docker run -d -p 5000:5000 --name facts-api cicd-test-app

# Run with environment variables
docker run -p 5000:5000 -e FLASK_ENV=production cicd-test-app
```

#### Manage
```bash
# List containers
docker ps

# Stop container
docker stop facts-api

# Remove container
docker rm facts-api

# View logs
docker logs facts-api
```

### ⚙️ **Step 9: Complete CI/CD Pipeline**

#### Automated Script
```bash
# Run complete pipeline
chmod +x run_tests.sh
./run_tests.sh
```

#### Manual Pipeline Commands
```bash
# 1. Code Quality
black --check .
isort --check-only .
flake8 . --count --select=E9,F63,F7,F82

# 2. All Tests
pytest test_comprehensive.py::TestHealthEndpoint \
       test_comprehensive.py::TestFactsEndpoints \
       test_comprehensive.py::TestUserAuthentication \
       --tb=no -q

# 3. Integration Tests  
pytest test_integration.py --tb=no -q

# 4. Performance Tests
pytest test_load.py::TestLoadAndPerformance::test_response_time_benchmarks --tb=no -q

# 5. Coverage
pytest --cov=app --cov=models --cov-report=term-missing --tb=no -q

# 6. Security Tests
pytest test_comprehensive.py::TestEdgeCases::test_sql_injection_attempts \
       test_comprehensive.py::TestDatabaseIntegration::test_password_hashing \
       --tb=no -q

# 7. Build & Deploy
docker build -t cicd-test-app .
docker run -d -p 5000:5000 --name facts-api cicd-test-app
```

### 🎯 **Step 10: Production Deployment**

#### Pre-deployment Checks
```bash
# Final test suite
pytest --tb=no

# Security scan (if tools available)
bandit -r .

# Dependency check
pip check

# Environment validation
python -c "from app import create_app; app=create_app(); print('✅ App configuration valid')"
```

#### Deployment Commands
```bash
# Container deployment
docker-compose up -d

# Kubernetes deployment (example)
kubectl apply -f k8s/

# Health check after deployment
curl http://your-domain.com/health

# Monitor logs
docker logs -f facts-api
```

## 📋 **Quick Reference**

### Most Common Commands
```bash
# Development cycle
pip install -r requirements.txt
black . && isort .
pytest -v
python app.py

# CI/CD cycle  
./run_tests.sh
docker build -t cicd-test-app .
docker run -p 5000:5000 cicd-test-app

# Testing subsets
pytest test_comprehensive.py::TestHealthEndpoint -v  # Unit tests
pytest test_integration.py -v                        # Integration tests  
pytest test_load.py -v                              # Performance tests
pytest --cov=app --cov-report=term-missing          # Coverage
```

### Test Categories
- **Unit Tests**: `test_comprehensive.py` (300+ tests)
- **Integration Tests**: `test_integration.py` (workflow tests)
- **Performance Tests**: `test_load.py` (load/response time tests)
- **Security Tests**: SQL injection, authentication, encryption
- **End-to-End Tests**: Complete user journeys

### Project Structure
```
cicd-test/
├── app.py                    # Main Flask application
├── models.py                 # Database models
├── config.py                 # Configuration settings
├── requirements.txt          # Dependencies
├── Dockerfile               # Container definition
├── pytest.ini              # Test configuration
├── run_tests.sh             # Complete CI/CD script
├── test_comprehensive.py    # Main test suite
├── test_integration.py      # Integration tests
├── test_load.py            # Performance tests
└── CI_CD_COMMANDS.md       # This file
```

## 🎉 **Success Criteria**
- ✅ All tests pass (Unit, Integration, Performance)
- ✅ Code quality checks pass
- ✅ Security tests pass
- ✅ Application starts successfully
- ✅ Docker image builds
- ✅ Endpoints respond correctly
- ✅ Coverage > 70%