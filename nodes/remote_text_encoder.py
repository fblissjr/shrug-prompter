# nodes/remote_text_encoder.py
import sys
import os
import json
import numpy as np
import torch
from typing import Dict, List, Union, Optional, Tuple

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from shrug_router import send_request
except ImportError:
    from ..shrug_router import send_request


class RemoteTextEncoder:
    """
    Remote text encoder that uses heylookitsanllm or other LLM servers
    to encode text into embeddings or conditioning vectors.
    
    This allows using powerful language models for text understanding
    and encoding, similar to CLIP text encoders but via API.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("VLM_CONTEXT",),
                "text": ("STRING", {"multiline": True}),
                "encoding_mode": (["embeddings", "conditioning", "semantic", "clip_style"], {
                    "default": "embeddings",
                    "tooltip": "embeddings: raw embeddings, conditioning: ready for diffusion models, semantic: meaning-preserving, clip_style: CLIP-like encoding"
                }),
                "output_dimension": ("INT", {
                    "default": 768,
                    "min": 128,
                    "max": 4096,
                    "step": 128,
                    "tooltip": "Target dimension for the encoding (model-dependent)"
                }),
                "normalize": ("BOOLEAN", {"default": True, "tooltip": "Normalize the output vectors"}),
                "pooling_strategy": (["mean", "max", "cls", "last"], {
                    "default": "mean",
                    "tooltip": "How to pool token embeddings: mean, max, CLS token, or last token"
                }),
            },
            "optional": {
                "batch_texts": ("LIST", {"tooltip": "List of texts to encode in batch"}),
                "encoding_instruction": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Optional instruction to guide the encoding (e.g., 'Encode for image generation')"
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
    
    def encode_text(self, context, text, encoding_mode="embeddings", output_dimension=768, 
                   normalize=True, pooling_strategy="mean", batch_texts=None, 
                   encoding_instruction="", cache_embeddings=True, debug_mode=False):
        """
        Encode text using remote LLM server as a text encoder.
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
            debug_info.append(f"Encoding {len(texts_to_encode)} text(s) in {encoding_mode} mode")
        
        # Check cache
        cache_key = self._generate_cache_key(texts_to_encode, encoding_mode, output_dimension, pooling_strategy)
        if cache_embeddings and cache_key in self._cache:
            if debug_mode:
                debug_info.append("Using cached embeddings")
            cached_result = self._cache[cache_key]
            return self._format_output(cached_result, debug_info, debug_mode)
        
        # Build the encoding request
        system_prompt = self._build_system_prompt(encoding_mode, encoding_instruction, output_dimension)
        
        # Format texts for the API
        if len(texts_to_encode) == 1:
            user_prompt = f"Encode the following text:\n\n{texts_to_encode[0]}"
        else:
            texts_formatted = "\n\n".join([f"[{i}] {txt}" for i, txt in enumerate(texts_to_encode)])
            user_prompt = f"Encode the following {len(texts_to_encode)} texts:\n\n{texts_formatted}"
        
        # Prepare API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Special parameters for encoding mode
        extra_params = {
            "response_format": {"type": "json_object"},  # Request JSON response
            "seed": 42,  # For reproducible embeddings
        }
        
        if encoding_mode == "embeddings":
            # Request raw embeddings if the model supports it
            extra_params["return_embeddings"] = True
        
        # Send request
        try:
            response = send_request(
                provider=provider_config["provider"],
                messages=messages,
                api_key=provider_config["api_key"],
                base_url=provider_config["base_url"],
                llm_model=provider_config["llm_model"],
                max_tokens=2048,  # Enough for embedding responses
                temperature=0.0,  # Deterministic for encoding
                top_p=1.0,
                timeout=60,
                **extra_params
            )
            
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                raise RuntimeError(f"API error: {error_msg}")
            
            # Extract embeddings from response
            embeddings = self._extract_embeddings(response, texts_to_encode, output_dimension, pooling_strategy, debug_mode)
            
            if normalize:
                embeddings = self._normalize_embeddings(embeddings)
            
            # Cache the result
            if cache_embeddings:
                self._cache[cache_key] = embeddings
                self._cleanup_cache()
            
            if debug_mode:
                debug_info.append(f"Successfully encoded {len(texts_to_encode)} texts")
                debug_info.append(f"Output shape: {embeddings.shape}")
            
            return self._format_output(embeddings, debug_info, debug_mode)
            
        except Exception as e:
            error_msg = f"Encoding failed: {str(e)}"
            if debug_mode:
                debug_info.append(error_msg)
                import traceback
                debug_info.append(traceback.format_exc())
            
            # Return zero embeddings on error
            zero_embeddings = torch.zeros((len(texts_to_encode), output_dimension))
            return self._format_output(zero_embeddings, debug_info, debug_mode)
    
    def _build_system_prompt(self, encoding_mode, instruction, dimension):
        """Build system prompt based on encoding mode."""
        base_prompt = "You are a text encoder that converts text into numerical representations."
        
        mode_prompts = {
            "embeddings": f"""Generate dense embedding vectors of dimension {dimension} for the input text.
Return a JSON object with an 'embeddings' field containing an array of {dimension} floating-point numbers.
The embeddings should capture the semantic meaning of the text.""",
            
            "conditioning": f"""Generate conditioning vectors suitable for diffusion models.
Return a JSON object with a 'conditioning' field containing an array of {dimension} numbers.
Focus on visual and stylistic elements that would guide image generation.""",
            
            "semantic": f"""Generate semantic encoding vectors that preserve meaning across languages and paraphrases.
Return a JSON object with a 'vectors' field containing an array of {dimension} numbers.
Ensure similar meanings produce similar vectors.""",
            
            "clip_style": f"""Generate CLIP-style text embeddings for the input.
Return a JSON object with a 'clip_embeddings' field containing an array of {dimension} numbers.
Optimize for alignment with visual concepts and cross-modal similarity."""
        }
        
        prompt = base_prompt + "\n\n" + mode_prompts.get(encoding_mode, mode_prompts["embeddings"])
        
        if instruction:
            prompt += f"\n\nAdditional encoding guidance: {instruction}"
        
        return prompt
    
    def _extract_embeddings(self, response, texts, dimension, pooling, debug_mode):
        """Extract embeddings from API response."""
        if "choices" not in response or not response["choices"]:
            raise ValueError("Invalid API response format")
        
        content = response["choices"][0]["message"]["content"]
        
        # Try to parse as JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract numbers from text
            import re
            numbers = re.findall(r'-?\d+\.?\d*', content)
            if len(numbers) >= dimension:
                data = {"embeddings": [float(n) for n in numbers[:dimension]]}
            else:
                # Generate random embeddings as fallback
                if debug_mode:
                    print(f"Warning: Could not parse embeddings, using random initialization")
                return torch.randn((len(texts), dimension))
        
        # Extract embedding array from various possible formats
        embedding_data = None
        for key in ["embeddings", "conditioning", "vectors", "clip_embeddings", "embedding", "vector"]:
            if key in data:
                embedding_data = data[key]
                break
        
        if embedding_data is None:
            # Try to find any array in the response
            for value in data.values():
                if isinstance(value, list) and len(value) > 0:
                    embedding_data = value
                    break
        
        if embedding_data is None:
            raise ValueError("No embedding data found in response")
        
        # Convert to tensor
        if isinstance(embedding_data[0], list):
            # Multiple embeddings
            embeddings = torch.tensor(embedding_data, dtype=torch.float32)
        else:
            # Single embedding
            embeddings = torch.tensor([embedding_data], dtype=torch.float32)
        
        # Ensure correct dimensions
        if embeddings.shape[1] != dimension:
            # Resize if needed
            if embeddings.shape[1] > dimension:
                embeddings = embeddings[:, :dimension]
            else:
                # Pad with zeros
                padding = torch.zeros((embeddings.shape[0], dimension - embeddings.shape[1]))
                embeddings = torch.cat([embeddings, padding], dim=1)
        
        # Ensure we have embeddings for all texts
        if embeddings.shape[0] < len(texts):
            # Duplicate last embedding if needed
            while embeddings.shape[0] < len(texts):
                embeddings = torch.cat([embeddings, embeddings[-1:]], dim=0)
        elif embeddings.shape[0] > len(texts):
            embeddings = embeddings[:len(texts)]
        
        return embeddings
    
    def _normalize_embeddings(self, embeddings):
        """Normalize embedding vectors."""
        norms = torch.norm(embeddings, p=2, dim=1, keepdim=True)
        return embeddings / (norms + 1e-8)
    
    def _generate_cache_key(self, texts, mode, dimension, pooling):
        """Generate cache key for embeddings."""
        import hashlib
        text_str = "|".join(texts)
        key_str = f"{text_str}_{mode}_{dimension}_{pooling}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _cleanup_cache(self):
        """Clean up cache if it gets too large."""
        if len(self._cache) > self._max_cache_size:
            # Remove oldest entries
            items = list(self._cache.items())
            for key, _ in items[:len(items)//2]:
                del self._cache[key]
    
    def _format_output(self, embeddings, debug_info, debug_mode):
        """Format output for ComfyUI."""
        # Create conditioning format (compatible with CLIP conditioning)
        # [[embeddings, {}]] format expected by many nodes
        conditioning = [[embeddings, {}]]
        
        # Create latent format
        latent = {"samples": embeddings.unsqueeze(0)}  # Add batch dimension
        
        # Get dimension
        dimension = embeddings.shape[1]
        
        # Format debug info
        debug_str = "\n".join(debug_info) if debug_mode else ""
        
        return (conditioning, latent, embeddings, dimension, debug_str)