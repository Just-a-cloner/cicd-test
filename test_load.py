import pytest
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean, median
import requests
from app import create_app
from config import TestConfig
from models import db

class TestLoadAndPerformance:
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
    
    @pytest.fixture
    def running_app(self, app):
        """Start the app in a separate thread for load testing"""
        import threading
        from werkzeug.serving import make_server
        
        server = make_server('127.0.0.1', 5001, app, threaded=True)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        
        # Give the server time to start
        time.sleep(0.5)
        yield 'http://127.0.0.1:5001'
        
        server.shutdown()
    
    def measure_response_time(self, client, endpoint, method='GET', json_data=None):
        """Measure response time for an endpoint"""
        start_time = time.time()
        
        if method == 'GET':
            response = client.get(endpoint)
        elif method == 'POST':
            response = client.post(endpoint, json=json_data)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return response_time, response.status_code
    
    def test_response_time_benchmarks(self, client):
        """Test that response times are within acceptable limits"""
        endpoints_to_test = [
            ('/health', 'GET'),
            ('/facts', 'GET'),
            ('/facts/random', 'GET'),
            ('/facts/categories', 'GET'),
        ]
        
        response_times = {}
        
        for endpoint, method in endpoints_to_test:
            times = []
            for _ in range(10):  # Test each endpoint 10 times
                response_time, status_code = self.measure_response_time(client, endpoint, method)
                if status_code == 200:
                    times.append(response_time)
            
            if times:
                response_times[endpoint] = {
                    'mean': mean(times),
                    'median': median(times),
                    'max': max(times),
                    'min': min(times)
                }
        
        # Assert reasonable response times (adjust thresholds as needed)
        for endpoint, stats in response_times.items():
            assert stats['mean'] < 500, f"{endpoint} average response time too high: {stats['mean']}ms"
            assert stats['max'] < 1000, f"{endpoint} max response time too high: {stats['max']}ms"
    
    def test_concurrent_requests_performance(self, client):
        """Test system performance under concurrent load"""
        def make_request():
            start_time = time.time()
            response = client.get('/facts/random')
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000,
                'success': response.status_code == 200
            }
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        results = {}
        
        for concurrency in concurrency_levels:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrency * 5)]
                responses = [future.result() for future in as_completed(futures)]
            
            successful_responses = [r for r in responses if r['success']]
            response_times = [r['response_time'] for r in successful_responses]
            
            if response_times:
                results[concurrency] = {
                    'success_rate': len(successful_responses) / len(responses),
                    'mean_response_time': mean(response_times),
                    'max_response_time': max(response_times)
                }
        
        # Verify performance doesn't degrade too much with higher concurrency
        for concurrency, stats in results.items():
            assert stats['success_rate'] >= 0.95, f"Success rate too low at concurrency {concurrency}: {stats['success_rate']}"
            # Response time shouldn't increase too dramatically with concurrency
            if concurrency > 1:
                assert stats['mean_response_time'] < 2000, f"Response time too high at concurrency {concurrency}"
    
    def test_database_performance_under_load(self, client):
        """Test database performance with multiple concurrent operations"""
        def register_and_use_user(user_id):
            user_data = {
                'username': f'loaduser{user_id}',
                'email': f'load{user_id}@test.com',
                'password': f'loadpass{user_id}'
            }
            
            # Register
            start_time = time.time()
            register_response = client.post('/register', json=user_data)
            register_time = time.time() - start_time
            
            if register_response.status_code != 201:
                return {'success': False, 'operation': 'register'}
            
            # Login
            start_time = time.time()
            login_response = client.post('/login', json={
                'username': user_data['username'],
                'password': user_data['password']
            })
            login_time = time.time() - start_time
            
            if login_response.status_code != 200:
                return {'success': False, 'operation': 'login'}
            
            # Use authenticated endpoints
            token = json.loads(login_response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            start_time = time.time()
            profile_response = client.get('/profile', headers=headers)
            profile_time = time.time() - start_time
            
            return {
                'success': profile_response.status_code == 200,
                'register_time': register_time * 1000,
                'login_time': login_time * 1000,
                'profile_time': profile_time * 1000
            }
        
        # Test with multiple concurrent users
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_and_use_user, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_results = [r for r in results if r['success']]
        success_rate = len(successful_results) / len(results)
        
        assert success_rate >= 0.9, f"Database operation success rate too low: {success_rate}"
        
        if successful_results:
            register_times = [r['register_time'] for r in successful_results]
            login_times = [r['login_time'] for r in successful_results]
            
            # Database operations should complete in reasonable time
            assert mean(register_times) < 1000, f"Average registration time too high: {mean(register_times)}ms"
            assert mean(login_times) < 500, f"Average login time too high: {mean(login_times)}ms"
    
    def test_memory_usage_stability(self, client):
        """Test that memory usage remains stable under load"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests to potentially cause memory leaks
        for i in range(100):
            client.get('/facts/random')
            client.get('/facts')
            client.get('/health')
            
            # Trigger garbage collection periodically
            if i % 20 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase < 50, f"Memory usage increased too much: {memory_increase}MB"
    
    def test_rate_limiting_effectiveness(self, client):
        """Test that rate limiting works correctly under load"""
        # Make rapid requests to trigger rate limiting
        responses = []
        
        for _ in range(15):  # Exceed typical rate limits
            response = client.post('/register', json={
                'username': f'ratetest{time.time()}',
                'email': f'rate{time.time()}@test.com',
                'password': 'testpass'
            })
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay between requests
        
        # Should get some rate limit responses (429)
        rate_limited_count = responses.count(429)
        
        # The rate limiter should kick in at some point
        # (This test might be flaky depending on the exact rate limiting implementation)
        assert rate_limited_count > 0 or any(code >= 400 for code in responses[5:]), \
            "Rate limiting doesn't seem to be working"
    
    def test_large_dataset_pagination_performance(self, client, app):
        """Test pagination performance with larger datasets"""
        # Add more facts to test pagination performance
        with app.app_context():
            from models import Fact
            
            # Add 100 more facts
            for i in range(100):
                fact = Fact(
                    content=f"Performance test fact {i}",
                    category="performance",
                    view_count=0
                )
                db.session.add(fact)
            db.session.commit()
        
        # Test pagination performance across different pages
        page_response_times = []
        
        for page in range(1, 11):  # Test first 10 pages
            start_time = time.time()
            response = client.get(f'/facts?page={page}&per_page=10')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            page_response_times.append(response_time)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['facts']) <= 10
        
        # Response times should be consistent across pages
        avg_response_time = mean(page_response_times)
        max_response_time = max(page_response_times)
        
        assert avg_response_time < 200, f"Average pagination response time too high: {avg_response_time}ms"
        assert max_response_time < 500, f"Max pagination response time too high: {max_response_time}ms"
    
    def test_error_handling_under_load(self, client):
        """Test that error handling remains robust under load"""
        def make_bad_request():
            # Make various types of bad requests
            bad_requests = [
                lambda: client.post('/register', json={'invalid': 'data'}),
                lambda: client.post('/login', json={'username': 'nonexistent'}),
                lambda: client.get('/facts/99999'),
                lambda: client.post('/favorites', json={'fact_id': 99999}),
                lambda: client.delete('/nonexistent'),
            ]
            
            import random
            bad_request = random.choice(bad_requests)
            response = bad_request()
            
            return {
                'status_code': response.status_code,
                'is_error': 400 <= response.status_code < 600,
                'is_server_error': response.status_code >= 500
            }
        
        # Make many concurrent bad requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_bad_request) for _ in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        # Count different types of responses
        client_errors = sum(1 for r in results if 400 <= r['status_code'] < 500)
        server_errors = sum(1 for r in results if r['status_code'] >= 500)
        
        # Should handle client errors gracefully
        assert client_errors > 0, "Expected some client errors for bad requests"
        
        # Should minimize server errors
        server_error_rate = server_errors / len(results)
        assert server_error_rate < 0.1, f"Too many server errors: {server_error_rate * 100}%"
        
        # System should still be responsive after handling errors
        health_response = client.get('/health')
        assert health_response.status_code == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-s'])