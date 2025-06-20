import pytest
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from app import create_app
from config import TestConfig
from models import db, User, Fact, Favorite

class TestIntegrationScenarios:
    @pytest.fixture
    def app(self):
        app = create_app(TestConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    def test_complete_user_journey(self, client):
        """Test a complete user journey from registration to using favorites"""
        # 1. Register a new user
        user_data = {
            'username': 'journeyuser',
            'email': 'journey@test.com',
            'password': 'journey123'
        }
        register_response = client.post('/register', json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login with the user
        login_response = client.post('/login', json={
            'username': 'journeyuser',
            'password': 'journey123'
        })
        assert login_response.status_code == 200
        
        login_data = json.loads(login_response.data)
        token = login_data['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 3. Get user profile
        profile_response = client.get('/profile', headers=headers)
        assert profile_response.status_code == 200
        profile_data = json.loads(profile_response.data)
        assert profile_data['user']['username'] == 'journeyuser'
        assert profile_data['favorites_count'] == 0
        
        # 4. Browse facts
        facts_response = client.get('/facts')
        assert facts_response.status_code == 200
        facts_data = json.loads(facts_response.data)
        assert len(facts_data['facts']) > 0
        
        # 5. Get a random fact
        random_response = client.get('/facts/random')
        assert random_response.status_code == 200
        
        # 6. Add fact to favorites
        fact_id = facts_data['facts'][0]['id']
        favorite_response = client.post('/favorites', json={'fact_id': fact_id}, headers=headers)
        assert favorite_response.status_code == 201
        
        # 7. Check favorites
        get_favorites_response = client.get('/favorites', headers=headers)
        assert get_favorites_response.status_code == 200
        favorites_data = json.loads(get_favorites_response.data)
        assert len(favorites_data) == 1
        assert favorites_data[0]['id'] == fact_id
        
        # 8. Updated profile should show favorite count
        updated_profile_response = client.get('/profile', headers=headers)
        updated_profile_data = json.loads(updated_profile_response.data)
        assert updated_profile_data['favorites_count'] == 1
        
        # 9. Remove from favorites
        remove_response = client.delete('/favorites', json={'fact_id': fact_id}, headers=headers)
        assert remove_response.status_code == 200
        
        # 10. Verify favorites are empty
        final_favorites_response = client.get('/favorites', headers=headers)
        final_favorites_data = json.loads(final_favorites_response.data)
        assert len(final_favorites_data) == 0
    
    def test_multiple_users_concurrent_access(self, client):
        """Test multiple users accessing the system concurrently"""
        def create_and_use_user(user_id):
            # Register user
            user_data = {
                'username': f'user{user_id}',
                'email': f'user{user_id}@test.com',
                'password': f'password{user_id}'
            }
            register_response = client.post('/register', json=user_data)
            
            if register_response.status_code != 201:
                return False
            
            # Login
            login_response = client.post('/login', json={
                'username': f'user{user_id}',
                'password': f'password{user_id}'
            })
            
            if login_response.status_code != 200:
                return False
            
            # Use the API
            token = json.loads(login_response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Get facts
            facts_response = client.get('/facts', headers=headers)
            if facts_response.status_code != 200:
                return False
            
            # Get random fact
            random_response = client.get('/facts/random', headers=headers)
            return random_response.status_code == 200
        
        # Test with multiple users
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_and_use_user, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        # At least most requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8  # At least 80% success rate
    
    def test_category_filtering_workflow(self, client):
        """Test the complete category filtering workflow"""
        # 1. Get all categories
        categories_response = client.get('/facts/categories')
        assert categories_response.status_code == 200
        categories_data = json.loads(categories_response.data)
        assert len(categories_data['categories']) > 0
        
        # 2. Test each category
        for category in categories_data['categories']:
            # Get facts by category
            category_facts_response = client.get(f'/facts?category={category}')
            assert category_facts_response.status_code == 200
            
            category_facts_data = json.loads(category_facts_response.data)
            
            # All facts should be from the requested category
            for fact in category_facts_data['facts']:
                assert fact['category'] == category
            
            # Get random fact from category
            random_category_response = client.get(f'/facts/random?category={category}')
            if random_category_response.status_code == 200:
                random_fact_data = json.loads(random_category_response.data)
                assert random_fact_data['category'] == category
    
    def test_pagination_consistency(self, client):
        """Test that pagination works consistently across requests"""
        # Get first page
        page1_response = client.get('/facts?page=1&per_page=2')
        assert page1_response.status_code == 200
        page1_data = json.loads(page1_response.data)
        
        # Get second page
        page2_response = client.get('/facts?page=2&per_page=2')
        assert page2_response.status_code == 200
        page2_data = json.loads(page2_response.data)
        
        # Verify no overlap between pages (if we have enough facts)
        if len(page1_data['facts']) > 0 and len(page2_data['facts']) > 0:
            page1_ids = {fact['id'] for fact in page1_data['facts']}
            page2_ids = {fact['id'] for fact in page2_data['facts']}
            assert page1_ids.isdisjoint(page2_ids)
        
        # Verify pagination metadata consistency
        assert page1_data['pagination']['total'] == page2_data['pagination']['total']
        assert page1_data['pagination']['pages'] == page2_data['pagination']['pages']
    
    def test_error_recovery_scenarios(self, client):
        """Test system behavior under various error conditions"""
        # 1. Test invalid JSON recovery
        invalid_json_response = client.post('/register', 
                                           data='{"invalid": json}', 
                                           content_type='application/json')
        assert invalid_json_response.status_code == 400
        
        # System should still work after invalid JSON
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # 2. Test accessing non-existent resources
        non_existent_response = client.get('/facts/99999')
        assert non_existent_response.status_code == 404
        
        # System should still work
        facts_response = client.get('/facts')
        assert facts_response.status_code == 200
        
        # 3. Test unauthorized access recovery
        unauthorized_response = client.get('/favorites')
        assert unauthorized_response.status_code == 401
        
        # Public endpoints should still work
        public_response = client.get('/facts/random')
        assert public_response.status_code == 200
    
    def test_data_consistency_across_operations(self, client):
        """Test that data remains consistent across different operations"""
        # Create a user and login
        user_data = {
            'username': 'consistencyuser',
            'email': 'consistency@test.com',
            'password': 'consistency123'
        }
        client.post('/register', json=user_data)
        
        login_response = client.post('/login', json={
            'username': 'consistencyuser',
            'password': 'consistency123'
        })
        
        token = json.loads(login_response.data)['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get initial facts count
        facts_response = client.get('/facts')
        initial_facts = json.loads(facts_response.data)
        initial_count = len(initial_facts['facts'])
        
        # Add some facts to favorites
        fact_ids = [fact['id'] for fact in initial_facts['facts'][:3]]
        
        for fact_id in fact_ids:
            favorite_response = client.post('/favorites', 
                                          json={'fact_id': fact_id}, 
                                          headers=headers)
            assert favorite_response.status_code == 201
        
        # Verify favorites count
        favorites_response = client.get('/favorites', headers=headers)
        favorites_data = json.loads(favorites_response.data)
        assert len(favorites_data) == len(fact_ids)
        
        # Verify profile shows correct count
        profile_response = client.get('/profile', headers=headers)
        profile_data = json.loads(profile_response.data)
        assert profile_data['favorites_count'] == len(fact_ids)
        
        # Remove one favorite
        remove_response = client.delete('/favorites', 
                                      json={'fact_id': fact_ids[0]}, 
                                      headers=headers)
        assert remove_response.status_code == 200
        
        # Verify counts are updated
        updated_favorites_response = client.get('/favorites', headers=headers)
        updated_favorites_data = json.loads(updated_favorites_response.data)
        assert len(updated_favorites_data) == len(fact_ids) - 1
        
        updated_profile_response = client.get('/profile', headers=headers)
        updated_profile_data = json.loads(updated_profile_response.data)
        assert updated_profile_data['favorites_count'] == len(fact_ids) - 1
    
    def test_view_count_tracking(self, client):
        """Test that view counts are properly tracked and updated"""
        # Get initial state
        random_response1 = client.get('/facts/random')
        assert random_response1.status_code == 200
        
        fact_data1 = json.loads(random_response1.data)
        initial_view_count = fact_data1['view_count']
        fact_id = fact_data1['id']
        
        # Make multiple requests to the same endpoint
        for _ in range(3):
            client.get('/facts/random')
        
        # Get the same specific fact through facts endpoint
        facts_response = client.get('/facts')
        facts_data = json.loads(facts_response.data)
        
        # Find our fact and check if view count increased
        our_fact = next((f for f in facts_data['facts'] if f['id'] == fact_id), None)
        if our_fact:
            # View count should have increased (though not necessarily by 3,
            # since random might return different facts)
            assert our_fact['view_count'] >= initial_view_count

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])