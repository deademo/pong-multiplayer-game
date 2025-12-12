"""
Pytest configuration and fixtures.
"""
import pytest
import os
import django
import asyncio
from django.conf import settings
from pong.consumers import ACTIVE_ROOMS

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def pytest_configure(config):
    """Configure pytest with Django settings."""
    if not settings.configured:
        # Determine which channel layer to use based on environment
        redis_url = os.environ.get('REDIS_URL')
        
        if redis_url:
            # Use Redis for integration tests (proper multi-connection support)
            channel_layers_config = {
                'default': {
                    'BACKEND': 'channels_redis.core.RedisChannelLayer',
                    'CONFIG': {
                        'hosts': [redis_url],
                    },
                }
            }
        else:
            # Use InMemory for unit tests (faster, but limited concurrency)
            channel_layers_config = {
                'default': {
                    'BACKEND': 'channels.layers.InMemoryChannelLayer'
                }
            }
        
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': os.environ.get('POSTGRES_DB', 'pong'),
                    'USER': os.environ.get('POSTGRES_USER', 'pong'),
                    'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'pongpassword'),
                    'HOST': os.environ.get('POSTGRES_HOST', 'db'),
                    'PORT': os.environ.get('POSTGRES_PORT', '5432'),
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'channels',
                'pong',
            ],
            CHANNEL_LAYERS=channel_layers_config,
            SECRET_KEY='test-secret-key',
            USE_TZ=True,
        )
        django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database."""
    pass


@pytest.fixture(autouse=True)
def cleanup_rooms():
    """Clean up ACTIVE_ROOMS between tests."""
    # Clear before test
    ACTIVE_ROOMS.clear()
    yield
    # Clear after test
    ACTIVE_ROOMS.clear()


@pytest.fixture(scope='function')
def event_loop():
    """Create a new event loop for each test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
