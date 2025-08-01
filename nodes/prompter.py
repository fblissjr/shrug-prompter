# In shrug-prompter/nodes/prompter.py
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from utils import tensors_to_base64_list, tensors_to_raw_bytes_list
    from shrug_router import send_request
    from api.capabilities_detector import CapabilityDetector
    from nodes.text_cleanup import TextCleanupNode
except ImportError:
    # Try relative imports as fallback
    from ..utils import tensors_to_base64_list, tensors_to_raw_bytes_list
    from ..shrug_router import send_request
    try:
        from ..api.capabilities_detector import CapabilityDetector
    except ImportError:
        CapabilityDetector = None
    try:
        from .text_cleanup import TextCleanupNode
    except ImportError:
        TextCleanupNode = None

import hashlib
import json

class ShrugPrompter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("VLM_CONTEXT",),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 32000}),
                "temperature": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 2.00, "step": 0.05, "display": "number"}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.00, "max": 1.00, "step": 0.01, "display": "number"}),
            },
            "optional": {
                "images": ("IMAGE",),
                "sampler_config": ("SAMPLER_CONFIG",),
                "mask": ("MASK",),
                "metadata": ("STRING", {"default": "{}"}),
                "template_vars": ("STRING", {"multiline": True, "default": "{}"}),
                "use_cache": ("BOOLEAN", {"default": False}),
                "debug_mode": ("BOOLEAN", {"default": False}),
                "batch_mode": ("BOOLEAN", {"default": False, "tooltip": "Process each image separately"}),
                "processing_mode": (["sequential", "sequential_with_context"], {"default": "sequential"}),
                "timeout": ("INT", {"default": 300, "min": 30, "max": 1800, "step": 30, "tooltip": "Request timeout in seconds"}),
                "extra_api_params": ("STRING", {"multiline": True, "default": "{}", "tooltip": "Additional API parameters as JSON (e.g. {\"seed\": 42, \"min_p\": 0.1})"}),
                "resize_mode": (["max", "width", "height", "exact", "none"], {"default": "max", "tooltip": "How to resize: max=maintain aspect, width/height=single dimension, exact=both dimensions, none=original"}),
                "resize_value": ("INT", {"default": 512, "min": 128, "max": 2048, "step": 64, "tooltip": "Size in pixels for resize_mode"}),
                "resize_width": ("INT", {"default": 512, "min": 128, "max": 2048, "step": 64, "tooltip": "Width for exact mode only"}),
                "resize_height": ("INT", {"default": 512, "min": 128, "max": 2048, "step": 64, "tooltip": "Height for exact mode only"}),
                "image_quality": ("INT", {"default": 85, "min": 1, "max": 100, "tooltip": "JPEG quality (1-100)"}),
                "preserve_alpha": ("BOOLEAN", {"default": False, "tooltip": "Keep transparency, output PNG"}),
                "response_cleanup": (["none", "basic", "standard", "strict"], {"default": "none", "tooltip": "none=no cleanup, basic=trim only, standard=trim+unicode+newlines, strict=ASCII only"}),
                "clear_cache": ("BOOLEAN", {"default": False, "tooltip": "Clear the cache before processing"}),
                "max_cache_size": ("INT", {"default": 10, "min": 0, "max": 100, "step": 5, "tooltip": "Maximum cache size (0 to disable cache completely)"}),
            },
        }

    RETURN_TYPES = ("*", "LIST", "STRING", "INT", "BOOLEAN", "STRING", "IMAGE")
    RETURN_NAMES = ("context", "response_texts", "first_response", "response_count", "is_batch_mode", "debug_info", "images")
    FUNCTION = "execute_prompt"
    CATEGORY = "Shrug Nodes/Logic"
    OUTPUT_IS_LIST = (False, False, False, False, False, False, False)

    def __init__(self):
        self._cache = {}
        self._cache_max_size = 10  # Reduced default cache size
        self._text_cleaner = None  # Reuse cleaner instance
        self._cache_hits = 0
        self._cache_misses = 0

    def execute_prompt(self, context, system_prompt, user_prompt, max_tokens, temperature, top_p, 
                          images=None, sampler_config=None, mask=None, metadata="{}", template_vars="{}", use_cache=True, debug_mode=False,
                          batch_mode=False, processing_mode="sequential", timeout=300, extra_api_params="{}", 
                          resize_mode="max", resize_value=512, resize_width=512, resize_height=512, 
                          image_quality=85, preserve_alpha=False, response_cleanup="none", clear_cache=False, max_cache_size=10):

        debug_info = []
        context["vlm_metadata"] = metadata
        context["debug_info"] = debug_info
        
        # Cache management
        if clear_cache:
            self._cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            print("[ShrugPrompter] Cache cleared")
        
        # Update max cache size
        self._cache_max_size = max_cache_size
        if max_cache_size == 0:
            use_cache = False  # Disable cache if max size is 0
            self._cache.clear()

        # Log initial state
        num_images = len(images) if images is not None and hasattr(images, '__len__') else 0
        if images is not None and hasattr(images, 'shape'):
            num_images = images.shape[0] if images.dim() == 4 else 1
        
        print(f"\n[ShrugPrompter] === Starting VLM Request ===")
        print(f"[ShrugPrompter] Images: {num_images}")
        print(f"[ShrugPrompter] Batch mode: {batch_mode}")
        print(f"[ShrugPrompter] Processing mode: {processing_mode}")
        print(f"[ShrugPrompter] Cache enabled: {use_cache} (size: {len(self._cache)}/{self._cache_max_size})")
        if use_cache and len(self._cache) > 0:
            print(f"[ShrugPrompter] Cache stats - hits: {self._cache_hits}, misses: {self._cache_misses}")
        print(f"[ShrugPrompter] Max tokens: {max_tokens}")
        
        if debug_mode:
            debug_info.append(f"Starting VLM request with {num_images} images")

        try:
            # The rest of the implementation is the same as previous answers.
            # This is the complete, correct logic.
            provider_config = context.get("provider_config")
            if not provider_config: raise ValueError("A `provider_config` is required.")
            
            print(f"[ShrugPrompter] Model: {provider_config.get('llm_model', 'unknown')}")
            print(f"[ShrugPrompter] Provider: {provider_config.get('provider', 'unknown')}")

            template_variables = json.loads(template_vars) if template_vars.strip() else {}
            processed_system = system_prompt.format(**template_variables)
            processed_user = user_prompt.format(**template_variables)
            
            # Parse extra API parameters
            try:
                extra_params = json.loads(extra_api_params) if extra_api_params.strip() else {}
                if debug_mode and extra_params:
                    debug_info.append(f"Extra API params: {extra_params}")
            except json.JSONDecodeError as e:
                print(f"[ShrugPrompter] ❌ Invalid JSON in extra_api_params: {e}")
                extra_params = {}
                if debug_mode:
                    debug_info.append(f"Failed to parse extra_api_params: {e}")

            # Extract top_k and repetition_penalty from sampler_config or use defaults
            top_k = 40
            repetition_penalty = 1.0
            if sampler_config and isinstance(sampler_config, dict):
                top_k = sampler_config.get("top_k", 40)
                repetition_penalty = sampler_config.get("repetition_penalty", 1.0)
                # Also update processing_mode and timeout if provided
                processing_mode = sampler_config.get("processing_mode", processing_mode)
                timeout = sampler_config.get("timeout", timeout)
                # Merge any extra parameters from sampler_config
                for key, value in sampler_config.items():
                    if key not in ["top_k", "repetition_penalty", "processing_mode", "timeout", "return_individual", "include_performance", "include_timing"]:
                        # These are API parameters, add to extra_params
                        extra_params[key] = value
            
            cache_key = self._create_cache_key(provider_config, processed_system, processed_user, max_tokens, temperature, top_p, top_k, repetition_penalty, images, mask)
            if use_cache and cache_key in self._cache:
                self._cache_hits += 1
                context["llm_response"] = self._cache[cache_key]
                print(f"[ShrugPrompter] Cache HIT! Using cached response")
                # Need to extract responses from cached data
                response_list = []
                cached_response = self._cache[cache_key]
                if isinstance(cached_response, dict) and "choices" in cached_response and cached_response["choices"]:
                    text = cached_response["choices"][0].get("message", {}).get("content", "")
                    response_list.append(text)
                else:
                    response_list.append(str(cached_response))
                
                first_response = response_list[0] if response_list else ""
                response_count = len(response_list)
                is_batch = False  # Cache is always single mode
                debug_output = "Response from cache" if debug_mode else "No debug info"
                
                return (context, response_list, first_response, response_count, is_batch, debug_output, images)
            
            # Cache miss
            self._cache_misses += 1

            # Check if we should use multipart
            use_multipart = False
            if CapabilityDetector and provider_config.get("base_url"):
                use_multipart = CapabilityDetector.should_use_multipart(provider_config["base_url"])
                if use_multipart:
                    print(f"[ShrugPrompter] Using multipart endpoint for better performance")
            
            # Process images based on endpoint type
            if use_multipart:
                # Get raw bytes for multipart
                image_bytes_list = tensors_to_raw_bytes_list(images, quality=image_quality, preserve_alpha=preserve_alpha)
                image_b64_list = None
            else:
                # Get base64 for standard endpoint
                image_b64_list = self._process_images(images, resize_mode, resize_value, resize_width, resize_height, image_quality, preserve_alpha)
                image_bytes_list = None
            mask_b64 = self._process_mask(mask)

            # Check if batch mode is enabled and we have multiple images
            # Need to check both b64 and bytes lists since multipart uses bytes
            images_list = image_b64_list or image_bytes_list or []
            if batch_mode and len(images_list) > 1:
                print(f"[ShrugPrompter] BATCH MODE: Processing {len(images_list)} images as separate API calls")
                if debug_mode:
                    debug_info.append(f"Batch mode: Processing {len(images_list)} images as separate inferences")
                
                # Each image gets its own inference
                response_data = self._build_and_execute_batch_request(
                    provider_config, processed_system, processed_user, image_b64_list, image_bytes_list,
                    mask_b64, max_tokens, temperature, top_p, top_k, repetition_penalty, processing_mode, debug_info, timeout, extra_params,
                    resize_mode, resize_value, resize_width, resize_height, image_quality, preserve_alpha, use_multipart, debug_mode
                )
                
                # Store multiple responses for batch mode
                context["llm_responses"] = response_data.get("completions", [])
                context["llm_response"] = response_data  # Keep full response for compatibility
                context["batch_mode"] = True
                context["batch_size"] = len(images_list)
            else:
                # Single request mode - can have multiple images in one conversation
                num_images = len(images_list)
                if num_images > 0:
                    print(f"[ShrugPrompter] SINGLE MODE: Processing {num_images} images in one API call")
                else:
                    print(f"[ShrugPrompter] TEXT-ONLY MODE: No images provided")
                    
                if debug_mode:
                    if image_b64_list:
                        debug_info.append(f"Single inference mode: Processing {len(image_b64_list)} image(s) together")
                    else:
                        debug_info.append("Text-only request (no images)")
                
                response_data = self._build_and_execute_request(provider_config, processed_system, processed_user, image_b64_list, image_bytes_list, mask_b64, max_tokens, temperature, top_p, top_k, repetition_penalty, timeout, extra_params, resize_mode, resize_value, resize_width, resize_height, image_quality, preserve_alpha, use_multipart, debug_mode)
                
                # Log response
                if "error" in response_data:
                    print(f"[ShrugPrompter] ❌ Request failed: {response_data['error'].get('message', 'Unknown error')}")
                else:
                    print(f"[ShrugPrompter] ✓ Request successful")
                
                context["llm_response"] = response_data
                context["batch_mode"] = False

                if use_cache and "error" not in response_data:
                    self._cache[cache_key] = response_data
                    self._cleanup_cache()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ShrugPrompter] ❌ Critical error: {str(e)}")
            print(f"[ShrugPrompter] Error type: {type(e).__name__}")
            print(f"[ShrugPrompter] Stack trace:\n{error_details}")
            context["llm_response"] = {"error": {"message": f"Critical error in ShrugPrompter: {str(e)}", "type": type(e).__name__, "details": error_details}}

        # Extract response list for direct output
        response_list = []
        
        if context.get("batch_mode") and "llm_responses" in context:
            # Batch mode - extract text from each response
            for resp in context["llm_responses"]:
                if isinstance(resp, dict):
                    # Check for batch response format with completions
                    if "completions" in resp:
                        for completion in resp["completions"]:
                            if "choices" in completion and completion["choices"]:
                                text = completion["choices"][0].get("message", {}).get("content", "")
                                response_list.append(text)
                    # Check for standard response format
                    elif "choices" in resp and resp["choices"]:
                        text = resp["choices"][0].get("message", {}).get("content", "")
                        # In batch mode, each response should be a single prompt
                        # But still parse in case it returns JSON
                        parsed = self._parse_response_smart(text, expected_count=1, debug_mode=debug_mode)
                        if isinstance(parsed, list) and len(parsed) == 1:
                            response_list.append(parsed[0])
                        elif isinstance(parsed, list):
                            # Unexpected - got multiple prompts from single image
                            if debug_mode:
                                print(f"[ShrugPrompter] Warning: Got {len(parsed)} prompts from single image")
                            response_list.extend(parsed)
                        else:
                            response_list.append(parsed)
                    elif "error" in resp:
                        response_list.append(f"Error: {resp['error'].get('message', 'Unknown error')}")
                    else:
                        # If we can't parse it, add the whole thing as string
                        response_list.append(str(resp))
                else:
                    response_list.append(str(resp))
        elif "llm_response" in context:
            # Single mode - extract single response
            resp = context["llm_response"]
            if isinstance(resp, dict) and "choices" in resp and resp["choices"]:
                text = resp["choices"][0].get("message", {}).get("content", "")
                # Smart parse the response - it might contain multiple prompts as JSON
                parsed = self._parse_response_smart(text, expected_count=num_images, debug_mode=debug_mode)
                if isinstance(parsed, list):
                    response_list.extend(parsed)
                else:
                    response_list.append(parsed)
            elif isinstance(resp, dict) and "error" in resp:
                response_list.append(f"Error: {resp['error'].get('message', 'Unknown error')}")
            else:
                response_list.append(str(resp))
        
        # Apply cleanup if requested
        if response_cleanup != "none" and TextCleanupNode:
            cleanup_ops_map = {
                "basic": "trim",
                "standard": "trim,unicode,newlines,collapse", 
                "strict": "trim,unicode,newlines,collapse,ascii"
            }
            
            if response_cleanup in cleanup_ops_map:
                operations = cleanup_ops_map[response_cleanup]
                # Reuse cleaner instance
                if not self._text_cleaner:
                    self._text_cleaner = TextCleanupNode()
                cleaner = self._text_cleaner
                cleaned_list = []
                
                # Debug logging of raw vs cleaned
                if debug_mode:
                    print(f"\n[ShrugPrompter] === Response Cleanup ({response_cleanup}) ===")
                
                for i, text in enumerate(response_list):
                    cleaned, original, _, _ = cleaner.cleanup_text(text, operations)
                    cleaned_list.append(cleaned)
                    
                    if debug_mode and original != cleaned:
                        print(f"\n[Response {i+1}] Raw:")
                        print(f"  {repr(original[:200])}{'...' if len(original) > 200 else ''}")
                        print(f"[Response {i+1}] Cleaned:")
                        print(f"  {repr(cleaned[:200])}{'...' if len(cleaned) > 200 else ''}")
                
                response_list = cleaned_list
                
                if debug_mode:
                    print(f"[ShrugPrompter] Cleanup complete - applied '{operations}'\n")
        
        # Get first response for convenience
        first_response = response_list[0] if response_list else ""
        
        # Get response count
        response_count = len(response_list)
        
        # Check if batch mode
        is_batch = context.get("batch_mode", False)
        
        # Debug log final responses
        if debug_mode:
            print(f"\n[ShrugPrompter] === Final Responses ===")
            for i, text in enumerate(response_list):
                # Show actual characters, not escape sequences
                preview = text[:150] + "..." if len(text) > 150 else text
                print(f"[{i+1}] {preview}")
            print()
        
        # Format debug info
        debug_output = "\n".join(debug_info) if debug_info else "No debug info"
        
        # Store cleaned responses in context for accumulator compatibility
        # Only store if cleanup was applied to avoid duplication
        if response_cleanup != "none":
            context["cleaned_responses"] = response_list
        
        print(f"[ShrugPrompter] === VLM Request Complete ===\n")
        return (context, response_list, first_response, response_count, is_batch, debug_output, images)

    # Helper methods are complete and do not require further changes.
    def _create_cache_key(self, provider_config, system, user, max_tokens, temp, top_p, top_k, repetition_penalty, images, mask):
        data = { 
            "provider": provider_config.get("provider"), 
            "model": provider_config.get("llm_model"), 
            "system": system, 
            "user": user, 
            "max_tokens": max_tokens, 
            "temperature": temp, 
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty,
            "images_shape": str(images.shape) if images is not None else "None", 
            "mask_shape": str(mask.shape) if mask is not None else "None" 
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def _cleanup_cache(self):
        """More efficient cache cleanup with LRU behavior"""
        if self._cache_max_size == 0:
            self._cache.clear()
            return
            
        if len(self._cache) > self._cache_max_size:
            # Remove oldest entries (FIFO order)
            num_to_remove = len(self._cache) - self._cache_max_size
            for key in list(self._cache.keys())[:num_to_remove]:
                del self._cache[key]
            print(f"[ShrugPrompter] Cache cleanup: removed {num_to_remove} old entries")

    def _process_images(self, images, resize_mode="max", resize_value=512, resize_width=512, resize_height=512, image_quality=85, preserve_alpha=False):
        """Process images with proper resize parameters for server-side resizing"""
        if images is None:
            return []
        
        # For now, we still use base64 encoding but don't resize client-side
        # The resize parameters will be passed to the API for server-side resizing
        # This avoids creating unnecessary copies in memory
        
        # Use original size - let server handle resizing
        return tensors_to_base64_list(images, max_size=None, quality=image_quality) if images is not None else []

    def _process_mask(self, mask):
        if mask is None: return None
        masks = tensors_to_base64_list(mask)
        return masks[0] if masks else None
    
    def _parse_response_smart(self, text, expected_count=None, debug_mode=False):
        """
        Intelligently parse response text that might contain JSON arrays or objects.
        Returns a list of prompts if multiple are detected, or the original text.
        """
        # First, try to detect if this looks like JSON
        text_stripped = text.strip()
        if not (text_stripped.startswith('[') or text_stripped.startswith('{')):
            # Not JSON, return as-is
            return text
        
        try:
            # Try to parse as JSON
            parsed = json.loads(text_stripped)
            
            # Case 1: Direct array of strings
            if isinstance(parsed, list):
                if all(isinstance(item, str) for item in parsed):
                    if debug_mode:
                        print(f"[ShrugPrompter] Detected JSON array with {len(parsed)} prompts")
                    return parsed
                # Array of objects - try to extract text fields
                elif all(isinstance(item, dict) for item in parsed):
                    prompts = []
                    for item in parsed:
                        # Look for common field names
                        for field in ['prompt', 'text', 'content', 'description', 'caption']:
                            if field in item:
                                prompts.append(str(item[field]))
                                break
                    if prompts and len(prompts) == len(parsed):
                        if debug_mode:
                            print(f"[ShrugPrompter] Extracted {len(prompts)} prompts from JSON objects")
                        return prompts
            
            # Case 2: Object with prompts array
            elif isinstance(parsed, dict):
                for field in ['prompts', 'results', 'outputs', 'texts', 'captions']:
                    if field in parsed and isinstance(parsed[field], list):
                        if all(isinstance(item, str) for item in parsed[field]):
                            if debug_mode:
                                print(f"[ShrugPrompter] Found {len(parsed[field])} prompts in JSON.{field}")
                            return parsed[field]
                
                # Single prompt in object
                for field in ['prompt', 'text', 'content', 'result', 'output']:
                    if field in parsed:
                        if debug_mode:
                            print(f"[ShrugPrompter] Found single prompt in JSON.{field}")
                        return str(parsed[field])
            
            # If we expected a certain count and got it, return the parsed result
            if expected_count and isinstance(parsed, list) and len(parsed) == expected_count:
                if debug_mode:
                    print(f"[ShrugPrompter] JSON array matches expected count {expected_count}")
                return [str(item) for item in parsed]
            
        except json.JSONDecodeError:
            if debug_mode:
                print(f"[ShrugPrompter] Text looks like JSON but failed to parse")
            pass
        
        # Return original text if no smart parsing applied
        return text

    def _build_and_execute_batch_request(self, provider_config, system, user, images_b64, images_bytes, mask, max_tokens, temp, top_p, top_k, repetition_penalty, processing_mode, debug_info, timeout=300, extra_params=None, resize_mode="max", resize_value=512, resize_width=512, resize_height=512, image_quality=85, preserve_alpha=False, use_multipart=False, debug_mode=False):
        """Execute batch request as separate API calls - simpler and more memory efficient"""
        import gc
        
        all_completions = []
        
        # Determine which image list to use
        if use_multipart and images_bytes:
            images_to_process = images_bytes
        else:
            images_to_process = images_b64 or []
        
        total_images = len(images_to_process)
        
        print(f"[ShrugPrompter] Starting batch processing of {total_images} images")
        print(f"[ShrugPrompter] Processing mode: {processing_mode}")
        
        # Process each image with a separate API call
        for i, img_data in enumerate(images_to_process):
            remaining = total_images - i - 1
            print(f"\n[ShrugPrompter] Processing image {i+1}/{total_images} (remaining: {remaining})")
            
            if debug_info:
                debug_info.append(f"Processing image {i+1}/{total_images}")
            
            # Build single-image request
            if use_multipart:
                # For multipart, use placeholder
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "text", "text": user},
                        {"type": "image_url", "image_url": {"url": "__RAW_IMAGE__"}}
                    ]}
                ]
            else:
                # For standard, use base64
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": [
                        {"type": "text", "text": user},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                    ]}
                ]
            
            # Make individual API call
            kwargs = {
                "provider": provider_config["provider"],
                "base_url": provider_config["base_url"],
                "api_key": provider_config["api_key"],
                "llm_model": provider_config["llm_model"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temp,
                "top_p": top_p,
                "timeout": timeout
            }
            
            # Add optional parameters only if not default
            if top_k > 0:
                kwargs["top_k"] = top_k
            if repetition_penalty != 1.0:
                kwargs["repetition_penalty"] = repetition_penalty
            
            # Add processing mode for batch calls
            kwargs["processing_mode"] = processing_mode
            
            # Only add mask if provided
            if mask:
                kwargs["mask"] = mask
            
            # Add resize parameters based on mode
            if resize_mode != "none":
                if resize_mode == "max":
                    kwargs["resize_max"] = resize_value
                    print(f"[ShrugPrompter] Setting resize_max={resize_value}")
                elif resize_mode == "width":
                    kwargs["resize_width"] = resize_value
                elif resize_mode == "height":
                    kwargs["resize_height"] = resize_value
                elif resize_mode == "exact":
                    kwargs["resize_width"] = resize_width
                    kwargs["resize_height"] = resize_height
            
            # Add quality and alpha settings
            kwargs["image_quality"] = image_quality
            kwargs["preserve_alpha"] = preserve_alpha
            
            # Debug: Show what resize params we're sending
            if resize_mode != "none":
                print(f"[ShrugPrompter] Resize params: mode={resize_mode}, value={resize_value}, quality={image_quality}")
            
            # Add raw images for multipart
            if use_multipart and images_bytes:
                # img_data is tuple of (bytes, mime_type)
                kwargs["raw_images"] = [img_data[0]]
            
            # Merge extra parameters
            if extra_params:
                kwargs.update(extra_params)
            
            try:
                response = send_request(**kwargs)
                
                # Log response info
                if "error" in response:
                    print(f"[ShrugPrompter] ❌ Image {i+1} failed: {response['error'].get('message', 'Unknown error')}")
                else:
                    content_preview = ""
                    if "choices" in response and response["choices"]:
                        content = response["choices"][0].get("message", {}).get("content", "")
                        content_preview = content[:100] + "..." if len(content) > 100 else content
                        content_preview = content_preview.replace('\n', ' ')
                    print(f"[ShrugPrompter] ✓ Image {i+1} complete: {content_preview}")
                
                all_completions.append(response)
            except Exception as e:
                # If one fails, record error but continue
                print(f"[ShrugPrompter] ❌ Image {i+1} exception: {str(e)}")
                error_response = {
                    "error": {"message": f"Failed processing image {i+1}: {str(e)}"}
                }
                all_completions.append(error_response)
            
            # Clean up memory after each image
            if i % 3 == 0:  # Every 3 images
                gc.collect()
        
        # Summary logging
        successful = sum(1 for r in all_completions if "error" not in r)
        failed = len(all_completions) - successful
        print(f"\n[ShrugPrompter] Batch complete: {successful} successful, {failed} failed")
        print(f"[ShrugPrompter] Total API calls made: {len(all_completions)}")
        
        # Return in batch format for compatibility
        return {
            "completions": all_completions,
            "processing_mode": processing_mode
        }

    def _build_and_execute_request(self, provider_config, system, user, images_b64, images_bytes, mask, max_tokens, temp, top_p, top_k, repetition_penalty, timeout=300, extra_params=None, resize_mode="max", resize_value=512, resize_width=512, resize_height=512, image_quality=85, preserve_alpha=False, use_multipart=False, debug_mode=False):
        if use_multipart and images_bytes:
            # For multipart, use placeholders
            user_content = [{"type": "text", "text": user}]
            for _ in images_bytes:
                user_content.append({"type": "image_url", "image_url": {"url": "__RAW_IMAGE__"}})
        else:
            # For standard, use base64
            user_content = [{"type": "text", "text": user}] + [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}} for img_b64 in (images_b64 or [])]
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user_content}]
        kwargs = {
            "provider": provider_config["provider"], 
            "base_url": provider_config["base_url"], 
            "api_key": provider_config["api_key"], 
            "llm_model": provider_config["llm_model"], 
            "messages": messages, 
            "max_tokens": max_tokens, 
            "temperature": temp, 
            "top_p": top_p, 
            "timeout": timeout
        }
        
        # Add optional parameters only if not default
        if top_k > 0:
            kwargs["top_k"] = top_k
        if repetition_penalty != 1.0:
            kwargs["repetition_penalty"] = repetition_penalty
        if mask:
            kwargs["mask"] = mask
        
        # Add resize parameters based on mode
        if resize_mode != "none":
            if resize_mode == "max":
                kwargs["resize_max"] = resize_value
            elif resize_mode == "width":
                kwargs["resize_width"] = resize_value
            elif resize_mode == "height":
                kwargs["resize_height"] = resize_value
            elif resize_mode == "exact":
                kwargs["resize_width"] = resize_width
                kwargs["resize_height"] = resize_height
        
        # Add quality and alpha settings
        kwargs["image_quality"] = image_quality
        kwargs["preserve_alpha"] = preserve_alpha
        
        # Add raw images for multipart
        if use_multipart and images_bytes:
            # Extract just the bytes from tuples
            kwargs["raw_images"] = [img[0] for img in images_bytes]
            
        # Merge extra parameters
        if extra_params:
            kwargs.update(extra_params)
        
        # Debug logging
        if debug_mode:
            print(f"\n[ShrugPrompter] === API Request Debug ===")
            print(f"Model: {provider_config['llm_model']}")
            print(f"Provider: {provider_config['provider']}")
            print(f"Max tokens: {max_tokens}")
            print(f"Temperature: {temp}")
            print(f"Images: {len(images_b64 or images_bytes or [])} {'(multipart)' if use_multipart else '(base64)'}")
            if resize_mode != "none":
                print(f"Resize: {resize_mode} = {resize_value if resize_mode != 'exact' else f'{resize_width}x{resize_height}'}")
            print(f"\nSystem prompt: {system[:100]}..." if len(system) > 100 else f"System prompt: {system}")
            print(f"User prompt: {user[:100]}..." if len(user) > 100 else f"User prompt: {user}")
            
        response = send_request(**kwargs)
        
        # Debug log raw response
        if debug_mode:
            print(f"\n[ShrugPrompter] === API Response Debug ===")
            if "error" in response:
                print(f"Error: {response['error']}")
            elif "choices" in response and response["choices"]:
                content = response["choices"][0].get("message", {}).get("content", "")
                print(f"Response content ({len(content)} chars):")
                print(f"{repr(content[:200])}{'...' if len(content) > 200 else ''}")
            print()
            
        return response
