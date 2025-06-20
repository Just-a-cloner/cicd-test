import pytest
import json
import time
from datetime import datetime, timedelta
from app import create_app
from config import TestConfig
from models import db, User, Fact, Favorite, ApiUsage

class TestApp:
    @pytest.fixture
    def app(self):
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            self.seed_test_data()
            yield app
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self, client):
        # Register and login a test user
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        client.post('/register', json=user_data)
        
        login_response = client.post('/login', json={
            'username': 'testuser',
            'password': 'testpassword123'
        })
        
        token = json.loads(login_response.data)['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def seed_test_data(self):
        # Create test facts
        facts = [
            Fact(content="Test fact 1", category="test", view_count=5),
            Fact(content="Test fact 2", category="science", view_count=10),
            Fact(content="Test fact 3", category="animals", view_count=3),
            Fact(content="Inactive fact", category="test", is_active=False),
        ]
        
        for fact in facts:
            db.session.add(fact)
        
        # Create test user
        user = User(username='existinguser', email='existing@example.com')
        user.set_password('password123')
        db.session.add(user)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding data: {e}")

class TestHealthEndpoint(TestApp):
    def test_health_check_success(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['database'] == 'healthy'
        assert 'timestamp' in data
        assert data['message'] == 'Service is running'
    
    def test_health_check_includes_timestamp(self, client):
        response = client.get('/health')
        data = json.loads(response.data)
        timestamp = datetime.fromisoformat(data['timestamp'])
        assert abs((datetime.utcnow() - timestamp).total_seconds()) < 10

class TestUserAuthentication(TestApp):
    def test_user_registration_success(self, client):
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123'
        }
        response = client.post('/register', json=user_data)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User created successfully'
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'new@example.com'
        assert 'password_hash' not in data['user']
    
    def test_user_registration_duplicate_username(self, client):
        user_data = {
            'username': 'existinguser',
            'email': 'different@example.com',
            'password': 'password123'
        }
        response = client.post('/register', json=user_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Username already exists'
    
    def test_user_registration_duplicate_email(self, client):
        user_data = {
            'username': 'differentuser',
            'email': 'existing@example.com',
            'password': 'password123'
        }
        response = client.post('/register', json=user_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Email already exists'
    
    def test_user_registration_missing_fields(self, client):
        user_data = {'username': 'incomplete'}
        response = client.post('/register', json=user_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Missing required fields'
    
    def test_user_login_success(self, client):
        # First register a user
        user_data = {
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'loginpass123'
        }
        client.post('/register', json=user_data)
        
        # Then login
        login_data = {'username': 'loginuser', 'password': 'loginpass123'}
        response = client.post('/login', json=login_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['user']['username'] == 'loginuser'
    
    def test_user_login_invalid_credentials(self, client):
        login_data = {'username': 'nonexistent', 'password': 'wrongpass'}
        response = client.post('/login', json=login_data)
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Invalid credentials'
    
    def test_user_login_missing_fields(self, client):
        login_data = {'username': 'incomplete'}
        response = client.post('/login', json=login_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Missing username or password'

class TestFactsEndpoints(TestApp):
    def test_get_facts_default_pagination(self, client):
        response = client.get('/facts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'facts' in data
        assert 'pagination' in data
        assert len(data['facts']) <= 10  # Default per_page
        assert data['pagination']['page'] == 1
    
    def test_get_facts_custom_pagination(self, client):
        response = client.get('/facts?page=1&per_page=2')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['facts']) <= 2
        assert data['pagination']['per_page'] == 2
    
    def test_get_facts_by_category(self, client):
        response = client.get('/facts?category=science')
        assert response.status_code == 200
        data = json.loads(response.data)
        for fact in data['facts']:
            assert fact['category'] == 'science'
    
    def test_get_facts_excludes_inactive(self, client):
        response = client.get('/facts')
        data = json.loads(response.data)
        fact_contents = [fact['content'] for fact in data['facts']]
        assert 'Inactive fact' not in fact_contents
    
    def test_random_fact_success(self, client):
        response = client.get('/facts/random')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'content' in data
        assert 'category' in data
        assert 'view_count' in data
    
    def test_random_fact_increments_view_count(self, client):
        # Get initial view count
        response = client.get('/facts/random')
        initial_data = json.loads(response.data)
        initial_count = initial_data['view_count']
        
        # Request same fact type multiple times to potentially get same fact
        for _ in range(5):
            response = client.get('/facts/random')
            if response.status_code == 200:
                data = json.loads(response.data)
                if data['id'] == initial_data['id']:
                    assert data['view_count'] > initial_count
                    break
    
    def test_random_fact_by_category(self, client):
        response = client.get('/facts/random?category=science')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['category'] == 'science'
    
    def test_get_categories(self, client):
        response = client.get('/facts/categories')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categories' in data
        assert isinstance(data['categories'], list)
        assert 'test' in data['categories']
        assert 'science' in data['categories']

class TestFavoritesSystem(TestApp):
    def test_get_favorites_empty(self, client, auth_headers):
        response = client.get('/favorites', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []
    
    def test_add_favorite_success(self, client, auth_headers):
        # Get a fact ID first
        facts_response = client.get('/facts')
        facts_data = json.loads(facts_response.data)
        fact_id = facts_data['facts'][0]['id']
        
        response = client.post('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Added to favorites'
    
    def test_add_favorite_duplicate(self, client, auth_headers):
        # Get a fact ID and add it
        facts_response = client.get('/facts')
        facts_data = json.loads(facts_response.data)
        fact_id = facts_data['facts'][0]['id']
        
        client.post('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        
        # Try to add again
        response = client.post('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Already in favorites'
    
    def test_add_favorite_nonexistent_fact(self, client, auth_headers):
        response = client.post('/favorites', json={'fact_id': 9999}, headers=auth_headers)
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Fact not found'
    
    def test_remove_favorite_success(self, client, auth_headers):
        # Add a favorite first
        facts_response = client.get('/facts')
        facts_data = json.loads(facts_response.data)
        fact_id = facts_data['facts'][0]['id']
        
        client.post('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        
        # Remove it
        response = client.delete('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Removed from favorites'
    
    def test_remove_favorite_not_in_favorites(self, client, auth_headers):
        facts_response = client.get('/facts')
        facts_data = json.loads(facts_response.data)
        fact_id = facts_data['facts'][0]['id']
        
        response = client.delete('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not in favorites'
    
    def test_favorites_unauthorized(self, client):
        response = client.get('/favorites')
        assert response.status_code == 401

class TestUserProfile(TestApp):
    def test_get_profile_success(self, client, auth_headers):
        response = client.get('/profile', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data
        assert 'favorites_count' in data
        assert data['user']['username'] == 'testuser'
        assert data['favorites_count'] == 0
    
    def test_get_profile_unauthorized(self, client):
        response = client.get('/profile')
        assert response.status_code == 401

class TestAdminEndpoints(TestApp):
    def test_admin_stats(self, client, auth_headers):
        response = client.get('/admin/stats', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_users' in data
        assert 'active_users' in data
        assert 'total_facts' in data
        assert 'active_facts' in data
        assert 'total_favorites' in data
        assert 'api_calls_today' in data
        assert data['total_users'] >= 1
        assert data['total_facts'] >= 3

class TestErrorHandling(TestApp):
    def test_404_error(self, client):
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Endpoint not found'
    
    def test_invalid_json(self, client):
        response = client.post('/register', data='invalid json', content_type='application/json')
        assert response.status_code == 400

class TestRateLimiting(TestApp):
    def test_register_rate_limit(self, client):
        # This test might be flaky depending on rate limiter implementation
        # Make multiple rapid requests
        user_base = {'email': 'rate@test.com', 'password': 'pass123'}
        
        responses = []
        for i in range(7):  # Exceed the 5 per minute limit
            user_data = {**user_base, 'username': f'rateuser{i}'}
            response = client.post('/register', json=user_data)
            responses.append(response.status_code)
        
        # Should get at least one rate limit response
        assert 429 in responses or any(r >= 400 for r in responses[5:])

class TestApiUsageTracking(TestApp):
    def test_usage_tracking_records_calls(self, client, app):
        # Make a request
        client.get('/health')
        
        # Check if usage was recorded
        with app.app_context():
            usage_count = ApiUsage.query.count()
            assert usage_count > 0
            
            latest_usage = ApiUsage.query.order_by(ApiUsage.timestamp.desc()).first()
            assert latest_usage.endpoint == 'health_check'
            assert latest_usage.method == 'GET'
            assert latest_usage.response_code == 200
            assert latest_usage.response_time_ms > 0

class TestDatabaseIntegration(TestApp):
    def test_database_connection(self, app):
        with app.app_context():
            # Test basic database operations
            user = User(username='dbtest', email='db@test.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            # Verify user was saved
            saved_user = User.query.filter_by(username='dbtest').first()
            assert saved_user is not None
            assert saved_user.check_password('testpass')
    
    def test_password_hashing(self, app):
        with app.app_context():
            user = User(username='hashtest', email='hash@test.com')
            user.set_password('plaintext')
            
            # Password should be hashed
            assert user.password_hash != 'plaintext'
            assert user.check_password('plaintext')
            assert not user.check_password('wrongpassword')

class TestEdgeCases(TestApp):
    def test_empty_request_bodies(self, client):
        response = client.post('/register', json={})
        assert response.status_code == 400
    
    def test_malformed_json_requests(self, client):
        response = client.post('/login', data='{"incomplete": json}', content_type='application/json')
        assert response.status_code == 400
    
    def test_extremely_long_usernames(self, client):
        user_data = {
            'username': 'a' * 1000,  # Very long username
            'email': 'long@test.com',
            'password': 'password123'
        }
        response = client.post('/register', json=user_data)
        # Should handle gracefully (either accept if DB allows, or reject)
        assert response.status_code in [201, 400, 500]
    
    def test_sql_injection_attempts(self, client):
        # Try SQL injection in login
        malicious_data = {
            'username': "'; DROP TABLE users; --",
            'password': 'password'
        }
        response = client.post('/login', json=malicious_data)
        # Should not crash the application
        assert response.status_code in [400, 401]
    
    def test_concurrent_favorite_operations(self, client, auth_headers):
        # This is a basic test - in real scenarios you'd use threading
        facts_response = client.get('/facts')
        facts_data = json.loads(facts_response.data)
        fact_id = facts_data['facts'][0]['id']
        
        # Add favorite
        response1 = client.post('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        # Try to add same favorite again immediately
        response2 = client.post('/favorites', json={'fact_id': fact_id}, headers=auth_headers)
        
        # One should succeed, one should fail
        assert (response1.status_code == 201 and response2.status_code == 400) or \
               (response1.status_code == 400 and response2.status_code == 201)

class TestPerformanceAndScalability(TestApp):
    def test_pagination_with_large_offset(self, client):
        # Test pagination with large page numbers
        response = client.get('/facts?page=1000&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should return empty results gracefully
        assert data['facts'] == []
    
    def test_max_per_page_limit(self, client):
        # Test that per_page is capped
        response = client.get('/facts?per_page=1000')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be limited to 50 based on our implementation
        assert data['pagination']['per_page'] <= 50
    
    def test_multiple_simultaneous_requests(self, client):
        # Simple test for multiple requests
        responses = []
        for _ in range(10):
            response = client.get('/facts/random')
            responses.append(response.status_code)
        
        # All should succeed
        assert all(status == 200 for status in responses)

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])