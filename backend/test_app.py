import pytest
import json
from unittest.mock import Mock
import sys

# Mock hardware libraries before importing app
sys.modules['rpi_ws281x'] = Mock()
sys.modules['RPi.GPIO'] = Mock()

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_hello_world(client):
    """Test the root endpoint returns Hello World."""
    response = client.get('/')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    
    data = json.loads(response.get_data(as_text=True))
    assert 'message' in data
    assert 'Hello World from Piano LED Visualizer Backend!' in data['message']
    assert data['status'] == 'running'
    assert data['version'] == '1.0.0'


def test_health_endpoint(client):
    """Test the health check endpoint returns correct status and format."""
    response = client.get('/health')
    
    # Check status code
    assert response.status_code == 200
    
    # Check content type
    assert response.content_type == 'application/json'
    
    # Parse JSON response
    data = json.loads(response.get_data(as_text=True))
    
    # Check required fields exist
    assert 'status' in data
    assert 'message' in data
    assert 'timestamp' in data
    
    # Check status value
    assert data['status'] == 'healthy'
    
    # Check message content
    assert 'Backend is running successfully' in data['message']
    
    # Check timestamp is a string (ISO format)
    assert isinstance(data['timestamp'], str)
    assert len(data['timestamp']) > 0


def test_health_endpoint_cors_headers(client):
    """Test that CORS headers are properly set on health endpoint."""
    response = client.get('/health')
    
    # Check CORS headers are present
    assert 'Access-Control-Allow-Origin' in response.headers
    

def test_404_error_handler(client):
    """Test that 404 errors are handled properly."""
    response = client.get('/nonexistent-endpoint')
    
    assert response.status_code == 404
    assert response.content_type == 'application/json'
    
    data = json.loads(response.get_data(as_text=True))
    assert 'error' in data
    assert data['error'] == 'Not Found'


def test_health_endpoint_multiple_calls(client):
    """Test that health endpoint works consistently across multiple calls."""
    for _ in range(3):
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.get_data(as_text=True))
        assert data['status'] == 'healthy'