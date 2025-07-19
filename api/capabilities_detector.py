"""Server capability detection for optimal performance"""
import requests
import json
from typing import Dict, Optional

class CapabilityDetector:
    """Detects server capabilities and optimizations"""
    
    _cache = {}  # Cache capabilities by base_url
    
    @classmethod
    def get_capabilities(cls, base_url: str) -> Optional[Dict]:
        """Get and cache server capabilities"""
        if base_url in cls._cache:
            return cls._cache[base_url]
        
        try:
            response = requests.get(f"{base_url}/v1/capabilities", timeout=2)
            if response.status_code == 200:
                capabilities = response.json()
                cls._cache[base_url] = capabilities
                
                # Log detected optimizations
                print(f"[Shrug-Prompter] Server capabilities detected for {base_url}:")
                opts = capabilities.get("optimizations", {})
                if opts.get("json", {}).get("orjson_available"):
                    print("  ✓ Fast JSON (3-10x speedup)")
                if opts.get("image", {}).get("turbojpeg_available"):
                    print("  ✓ TurboJPEG (4-10x faster JPEG)")
                if opts.get("image", {}).get("xxhash_available"):
                    print("  ✓ xxHash (50x faster hashing)")
                
                # Check multipart endpoint
                if capabilities.get("endpoints", {}).get("fast_vision", {}).get("available"):
                    print("  ✓ Multipart endpoint (57ms faster per image)")
                
                return capabilities
        except Exception as e:
            print(f"[Shrug-Prompter] Could not detect server capabilities: {e}")
        
        cls._cache[base_url] = None
        return None
    
    @classmethod
    def should_use_multipart(cls, base_url: str) -> bool:
        """Check if multipart endpoint should be used"""
        caps = cls.get_capabilities(base_url)
        if not caps:
            return False
        
        return caps.get("recommendations", {}).get("vision_models", {}).get("use_multipart", False)
    
    @classmethod
    def get_optimal_batch_size(cls, base_url: str) -> int:
        """Get recommended batch size"""
        caps = cls.get_capabilities(base_url)
        if not caps:
            return 4  # Default
        
        return caps.get("recommendations", {}).get("batch_size", {}).get("optimal", 4)