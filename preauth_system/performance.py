"""
Simplified performance module - basic caching only.
Following CLAUDE.md principles.
"""

import time
from typing import Any, Optional, Dict


class SimpleCache:
    """Basic in-memory cache."""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        """Get value from cache."""
        return self.cache.get(str(key))
    
    def put(self, key, value, ttl=None):
        """Put value in cache."""
        self.cache[str(key)] = value
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()


# Global cache instance
_preauth_cache = SimpleCache()


def get_preauth_cache():
    """Get the global cache instance."""
    return _preauth_cache


def get_performance_optimizer():
    """Basic performance optimizer."""
    return {"enabled": True}


def get_cost_tracker():
    """Basic cost tracker."""
    return {"total_cost": 0.0}


def get_resource_monitor():
    """Basic resource monitor."""
    return {"memory_usage": 0}


def cached_function(func):
    """Simple caching decorator."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper