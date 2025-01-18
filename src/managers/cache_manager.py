from typing import Any, Optional, Dict, Union
from pathlib import Path
import json
import time
import pickle
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib

class CacheManager:
    """Manages both memory and disk caching with intelligent cache invalidation"""
    
    def __init__(self, cache_dir: Union[str, Path], max_memory_items: int = 1000,
                 default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory cache settings
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.max_memory_items = max_memory_items
        self.default_ttl = default_ttl
        
        # Thread pool for disk operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize cache directories
        self._init_cache_dirs()
        
        logging.info(f"Cache Manager initialized with directory: {self.cache_dir}")
        
    def _init_cache_dirs(self):
        """Initialize cache directory structure"""
        (self.cache_dir / "data").mkdir(exist_ok=True)
        (self.cache_dir / "meta").mkdir(exist_ok=True)
        
    def _generate_key(self, key: str) -> str:
        """Generate a safe cache key"""
        return hashlib.sha256(key.encode()).hexdigest()
        
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache, trying memory first then disk"""
        safe_key = self._generate_key(key)
        
        # Try memory cache first
        if safe_key in self.memory_cache:
            cache_data = self.memory_cache[safe_key]
            if time.time() < cache_data['expires']:
                return cache_data['value']
            else:
                del self.memory_cache[safe_key]
        
        # Try disk cache
        try:
            loop = asyncio.get_event_loop()
            cache_data = await loop.run_in_executor(
                self._executor, self._read_from_disk, safe_key
            )
            if cache_data:
                # Update memory cache
                self._update_memory_cache(safe_key, cache_data['value'], 
                                       cache_data['expires'])
                return cache_data['value']
        except Exception as e:
            logging.error(f"Error reading from disk cache: {str(e)}")
            
        return default
        
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in both memory and disk cache"""
        safe_key = self._generate_key(key)
        expires = time.time() + (ttl or self.default_ttl)
        
        # Update memory cache
        self._update_memory_cache(safe_key, value, expires)
        
        # Update disk cache
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._write_to_disk,
                safe_key,
                {'value': value, 'expires': expires}
            )
            return True
        except Exception as e:
            logging.error(f"Error writing to disk cache: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete value from both memory and disk cache"""
        safe_key = self._generate_key(key)
        
        # Remove from memory cache
        self.memory_cache.pop(safe_key, None)
        
        # Remove from disk cache
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._delete_from_disk,
                safe_key
            )
            return True
        except Exception as e:
            logging.error(f"Error deleting from disk cache: {str(e)}")
            return False
            
    async def clear(self) -> bool:
        """Clear all cache data"""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._clear_disk_cache
            )
            return True
        except Exception as e:
            logging.error(f"Error clearing cache: {str(e)}")
            return False
            
    def _update_memory_cache(self, key: str, value: Any, expires: float):
        """Update memory cache with LRU eviction"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest item
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['expires'])
            del self.memory_cache[oldest_key]
            
        self.memory_cache[key] = {
            'value': value,
            'expires': expires
        }
        
    def _write_to_disk(self, key: str, data: Dict[str, Any]):
        """Write cache data to disk"""
        data_file = self.cache_dir / "data" / f"{key}.pickle"
        meta_file = self.cache_dir / "meta" / f"{key}.json"
        
        # Write data
        with open(data_file, 'wb') as f:
            pickle.dump(data['value'], f)
            
        # Write metadata
        with open(meta_file, 'w') as f:
            json.dump({'expires': data['expires']}, f)
            
    def _read_from_disk(self, key: str) -> Optional[Dict[str, Any]]:
        """Read cache data from disk"""
        data_file = self.cache_dir / "data" / f"{key}.pickle"
        meta_file = self.cache_dir / "meta" / f"{key}.json"
        
        if not data_file.exists() or not meta_file.exists():
            return None
            
        try:
            # Read metadata
            with open(meta_file, 'r') as f:
                meta = json.load(f)
                
            # Check expiration
            if time.time() >= meta['expires']:
                self._delete_from_disk(key)
                return None
                
            # Read data
            with open(data_file, 'rb') as f:
                value = pickle.load(f)
                
            return {
                'value': value,
                'expires': meta['expires']
            }
        except Exception as e:
            logging.error(f"Error reading cache from disk: {str(e)}")
            return None
            
    def _delete_from_disk(self, key: str):
        """Delete cache data from disk"""
        data_file = self.cache_dir / "data" / f"{key}.pickle"
        meta_file = self.cache_dir / "meta" / f"{key}.json"
        
        if data_file.exists():
            data_file.unlink()
        if meta_file.exists():
            meta_file.unlink()
            
    def _clear_disk_cache(self):
        """Clear all disk cache data"""
        for file in (self.cache_dir / "data").glob("*.pickle"):
            file.unlink()
        for file in (self.cache_dir / "meta").glob("*.json"):
            file.unlink()
            
    @lru_cache(maxsize=1000)
    def _compute_hash(self, value: str) -> str:
        """Compute hash for cache key (LRU cached)"""
        return hashlib.sha256(value.encode()).hexdigest()
        
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern"""
        count = 0
        keys_to_delete = []
        
        # Check memory cache
        for key in self.memory_cache.keys():
            if pattern in key:
                keys_to_delete.append(key)
                count += 1
                
        # Delete from memory
        for key in keys_to_delete:
            del self.memory_cache[key]
            
        # Check disk cache
        try:
            data_files = list((self.cache_dir / "data").glob("*.pickle"))
            for file in data_files:
                key = file.stem
                if pattern in key:
                    await self.delete(key)
                    count += 1
        except Exception as e:
            logging.error(f"Error during pattern invalidation: {str(e)}")
            
        return count
        
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_size = len(self.memory_cache)
        disk_size = len(list((self.cache_dir / "data").glob("*.pickle")))
        
        return {
            'memory_items': memory_size,
            'disk_items': disk_size,
            'memory_limit': self.max_memory_items,
            'cache_dir': str(self.cache_dir)
        } 