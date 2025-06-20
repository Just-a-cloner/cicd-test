import pytest
import json
from app import app, RANDOM_FACTS

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['message'] == 'Service is running'

def test_random_fact(client):
    response = client.get('/fact')
    assert response.status_code == 200
    fact = response.data.decode('utf-8')
    assert fact in RANDOM_FACTS
    assert len(fact) > 0

def test_random_fact_returns_different_facts(client):
    facts = set()
    for _ in range(20):
        response = client.get('/fact')
        fact = response.data.decode('utf-8')
        facts.add(fact)
    
    # Should get at least 2 different facts in 20 requests (very high probability)
    assert len(facts) >= 2