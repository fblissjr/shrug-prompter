# nodes/remote_text_encoder.py
import sys
import os
import json
import numpy as np
import torch
import requests
from typing import Dict, List, Union, Optional, Tuple

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class RemoteTextEncoder:
    """
    Remote text encoder that uses heylookitsanllm's embeddings endpoint
    to get real model embeddings for text.
    
    This node sends text to the /v1/embeddings endpoint and receives
    actual model embeddings back, not hallucinated numbers.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("VLM_CONTEXT",),
                "text": ("STRING", {"multiline": True}),
                "normalize": ("BOOLEAN", {"default": True, "tooltip": "Normalize the output vectors"}),
            },
            "optional": {
                "batch_texts": ("LIST", {"tooltip": "List of texts to encode in batch"}),
                "dimensions": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4096,
                    "tooltip": "Truncate embeddings to this dimension (0 = use full dimension)"
                }),
                "cache_embeddings": ("BOOLEAN", {"default": True}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "LATENT", "FLOAT", "INT", "STRING")
    RETURN_NAMES = ("conditioning", "latent", "embedding_tensor", "dimension", "debug_info")
    FUNCTION = "encode_text"
    CATEGORY = "Shrug Nodes/Text"
    
    def __init__(self):
        self._cache = {}
        self._max_cache_size = 100
    
    def encode_text(self, context, text, normalize=True, batch_texts=None, 
                   dimensions=0, cache_embeddings=True, debug_mode=False):
        """
        Get real embeddings from the heylookitsanllm embeddings endpoint.
        """
        debug_info = []
        
        # Extract provider config
        provider_config = context.get("provider_config", {})
        if not provider_config:
            raise ValueError("No provider configuration found in context")
        
        # Prepare texts to encode
        texts_to_encode = []
        if batch_texts and isinstance(batch_texts, list):
            texts_to_encode = batch_texts
        else:
            texts_to_encode = [text]
        
        if debug_mode:
            debug_info.append(f"Encoding {len(texts_to_encode)} text(s)")
            debug_info.append(f"Using model: {provider_config.get('llm_model', 'default')}")
        
        # Check cache
        cache_key = self._generate_cache_key(texts_to_encode, dimensions, normalize)
        if cache_embeddings and cache_key in self._cache:
            if debug_mode:
                debug_info.append("Using cached embeddings")
            cached_result = self._cache[cache_key]
            return self._format_output(cached_result, debug_info, debug_mode)
        
        # Build embeddings API request
        base_url = provider_config.get("base_url", "http://localhost:8080").rstrip("/")
        embeddings_url = f"{base_url}/v1/embeddings"
        
        # Format request
        request_data = {
            "input": texts_to_encode if len(texts_to_encode) > 1 else texts_to_encode[0],
            "model": provider_config.get("llm_model", "default")
        }
        
        if dimensions > 0:
            request_data["dimensions"] = dimensions
        
        # Add auth header if API key provided
        headers = {"Content-Type": "application/json"}
        if provider_config.get("api_key"):
            headers["Authorization"] = f"Bearer {provider_config['api_key']}"
        
        if debug_mode:
            debug_info.append(f"Sending request to: {embeddings_url}")
            debug_info.append(f"Request: {json.dumps(request_data, indent=2)}")
        
        try:
            # Send request to embeddings endpoint
            response = requests.post(
                embeddings_url,
                headers=headers,
                json=request_data,
                timeout=30
            )
            
            if debug_mode:
                debug_info.append(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                # Try to get error message
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", str(error_data))
                except:
                    error_msg = response.text
                
                # Check if embeddings endpoint doesn't exist
                if response.status_code == 404:
                    error_msg = (
                        "Embeddings endpoint not found. "
                        "Please ensure heylookitsanllm has /v1/embeddings endpoint implemented. "
                        "See docs/heylookllm_embeddings_spec.md for implementation details."
                    )
                
                raise RuntimeError(f"Embeddings API error ({response.status_code}): {error_msg}")
            
            # Parse response
            response_data = response.json()
            
            if debug_mode:
                debug_info.append(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
            
            # Extract embeddings from OpenAI-compatible format
            if "data" not in response_data:
                raise ValueError("Invalid response format: missing 'data' field")
            
            embeddings_list = []
            for item in response_data["data"]:
                if "embedding" not in item:
                    raise ValueError("Invalid response format: missing 'embedding' field")
                embeddings_list.append(item["embedding"])
            
            # Convert to tensor
            embeddings = torch.tensor(embeddings_list, dtype=torch.float32)
            
            # Normalize if requested
            if normalize:
                embeddings = self._normalize_embeddings(embeddings)
            
            # Cache the result
            if cache_embeddings:
                self._cache[cache_key] = embeddings
                self._cleanup_cache()
            
            if debug_mode:
                debug_info.append(f"Successfully retrieved embeddings")
                debug_info.append(f"Shape: {embeddings.shape}")
                debug_info.append(f"Dimension: {embeddings.shape[1]}")
                if normalize:
                    debug_info.append("Embeddings normalized")
            
            return self._format_output(embeddings, debug_info, debug_mode)
            
        except requests.exceptions.ConnectionError:
            error_msg = (
                "Could not connect to embeddings endpoint. "
                "Please ensure heylookitsanllm is running and has embeddings support."
            )
            if debug_mode:
                debug_info.append(error_msg)
            raise RuntimeError(error_msg)
            
        except requests.exceptions.Timeout:
            error_msg = "Request to embeddings endpoint timed out"
            if debug_mode:
                debug_info.append(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            error_msg = f"Encoding failed: {str(e)}"
            if debug_mode:
                debug_info.append(error_msg)
                import traceback
                debug_info.append(traceback.format_exc())
            raise RuntimeError(error_msg)
    
    def _normalize_embeddings(self, embeddings):
        """Normalize embedding vectors to unit length."""
        norms = torch.norm(embeddings, p=2, dim=1, keepdim=True)
        return embeddings / (norms + 1e-8)
    
    def _generate_cache_key(self, texts, dimensions, normalize):
        """Generate cache key for embeddings."""
        import hashlib
        text_str = "|".join(texts)
        key_str = f"{text_str}_{dimensions}_{normalize}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _cleanup_cache(self):
        """Clean up cache if it gets too large."""
        if len(self._cache) > self._max_cache_size:
            # Remove oldest entries (first half)
            items = list(self._cache.items())
            for key, _ in items[:len(items)//2]:
                del self._cache[key]
    
    def _format_output(self, embeddings, debug_info, debug_mode):
        """Format output for ComfyUI."""
        # Create conditioning format (compatible with CLIP conditioning)
        # [[embeddings, {}]] format expected by many nodes
        conditioning = [[embeddings, {}]]
        
        # Create latent format (add batch dimension)
        latent = {"samples": embeddings.unsqueeze(0)}
        
        # Get dimension
        dimension = embeddings.shape[1]
        
        # Format debug info
        debug_str = "\n".join(debug_info) if debug_mode else ""
        
        return (conditioning, latent, embeddings, dimension, debug_str)