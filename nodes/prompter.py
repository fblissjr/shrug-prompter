# nodes/prompter.py
"""
Unified ShrugPrompter with all fixes and enhancements.
Backward compatible with existing workflows.
"""

try:
    from ..utils import tensors_to_base64_list, run_async
    from ..shrug_router import send_request
except ImportError:
    from utils import tensors_to_base64_list, run_async
    from shrug_router import send_request

import hashlib
import json

class ShrugPrompter:
    """
    Unified VLM prompter with template support, caching, and enhanced debugging.
    Backward compatible with existing workflows.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_tokens": ("INT", {"default": 256, "min": 1, "max": 4096}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0}),
            },
            "optional": {
                "images": ("IMAGE",),
                "mask": ("MASK",),
                "template_vars": ("STRING", {"multiline": True, "default": "{}"}),  # JSON string of variables
                "use_cache": ("BOOLEAN", {"default": True}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("*", "STRING")
    RETURN_NAMES = ("context", "debug_info")
    FUNCTION = "execute_prompt"
    CATEGORY = "Shrug Nodes/Logic"

    def __init__(self):
        # Simple in-memory cache for this session
        self._cache = {}
        self._cache_max_size = 50  # Keep it reasonable

    def _simple_template_render(self, template: str, variables: dict) -> str:
        """Simple template variable substitution for {{variable}} syntax."""
        if not variables:
            return template

        # Replace {{variable}} with values
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value))

        return template

    def _create_cache_key(self, provider_config: dict, system_prompt: str, user_prompt: str,
                         max_tokens: int, temperature: float, top_p: float,
                         images=None, mask=None) -> str:
        """Create a simple cache key for the request."""

        cache_data = {
            "provider": provider_config["provider"],
            "model": provider_config["llm_model"],
            "system": system_prompt,
            "user": user_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

        # Add image/mask signatures if present
        if images is not None:
            cache_data["images_shape"] = str(images.shape)
        if mask is not None:
            cache_data["mask_shape"] = str(mask.shape)

        # Create cache key
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _cleanup_cache(self):
        """Simple cache cleanup when it gets too large."""
        if len(self._cache) > self._cache_max_size:
            # Remove oldest half of entries
            keys_to_remove = list(self._cache.keys())[:(len(self._cache) // 2)]
            for key in keys_to_remove:
                del self._cache[key]

    def _extract_performance_metrics(self, response_data: dict, debug_info: list):
        """Extract performance metrics from heylookitsanllm response for debug display."""
        try:
            # Look for timing information in response (heylookitsanllm/ollama format)
            metrics = {}

            if isinstance(response_data, dict):
                # Total duration (nanoseconds to seconds)
                if 'total_duration' in response_data:
                    total_sec = response_data['total_duration'] / 1_000_000_000
                    metrics['total_time'] = f"{total_sec:.1f}s"

                # Model loading time
                if 'load_duration' in response_data:
                    load_sec = response_data['load_duration'] / 1_000_000_000
                    metrics['load_time'] = f"{load_sec:.1f}s"

                # Token generation speed
                if 'eval_count' in response_data and 'eval_duration' in response_data:
                    eval_count = response_data['eval_count']
                    eval_duration = response_data['eval_duration']
                    if eval_duration > 0:
                        tokens_per_sec = eval_count / eval_duration * 1_000_000_000
                        metrics['tokens_per_sec'] = f"{tokens_per_sec:.1f} tok/s"
                        metrics['response_tokens'] = f"{eval_count} tokens"

                # Prompt processing
                if 'prompt_eval_count' in response_data:
                    prompt_tokens = response_data['prompt_eval_count']
                    metrics['prompt_tokens'] = f"{prompt_tokens} tokens"

                # Inference time
                if 'eval_duration' in response_data:
                    inference_sec = response_data['eval_duration'] / 1_000_000_000
                    metrics['inference_time'] = f"{inference_sec:.1f}s"

            # Format metrics for debug output
            if metrics:
                debug_info.append("📊 Performance Metrics:")
                for key, value in metrics.items():
                    if key == 'tokens_per_sec':
                        debug_info.append(f"  ⚡ Processing speed: {value}")
                    elif key == 'load_time':
                        debug_info.append(f"  🔄 Model load time: {value}")
                    elif key == 'inference_time':
                        debug_info.append(f"  🧠 Inference time: {value}")
                    elif key == 'total_time':
                        debug_info.append(f"  ⏱️ Total time: {value}")
                    elif key == 'response_tokens':
                        debug_info.append(f"  📝 Response: {value}")
                    elif key == 'prompt_tokens':
                        debug_info.append(f"  📋 Prompt: {value}")

        except Exception as e:
            debug_info.append(f"Note: Could not extract performance metrics: {e}")

    def execute_prompt(self, context, system_prompt, user_prompt, max_tokens, temperature, top_p,
                          images=None, mask=None, template_vars="{}", use_cache=True, debug_mode=False):
        """Execute the VLM prompt request with all enhancements."""

        debug_info = []

        try:
            # Extract provider configuration
            provider_config = context.get("provider_config")
            if not provider_config:
                raise ValueError("A `provider_config` from a ShrugProviderSelector is required.")

            if debug_mode:
                debug_info.append(f"Using model: {provider_config.get('llm_model', 'unknown')}")

            # Parse template variables and process templates
            template_variables = self._parse_template_vars(template_vars, debug_info, debug_mode)
            processed_system, processed_user = self._process_templates(
                system_prompt, user_prompt, template_variables, debug_info, debug_mode
            )

            # Handle caching
            cached_response = self._handle_cache_lookup(
                use_cache, provider_config, processed_system, processed_user,
                max_tokens, temperature, top_p, images, mask, debug_info, debug_mode
            )
            if cached_response:
                if debug_mode:
                    context["debug_info"] = debug_info
                return (context,)

            # Process images and masks
            image_b64_list = self._process_images(images, debug_info, debug_mode)
            if image_b64_list is None:  # Error occurred
                context["llm_response"] = {"error": {"message": "Failed to process images"}}
                if debug_mode:
                    context["debug_info"] = debug_info
                return (context,)

            mask_b64 = self._process_mask(mask, debug_info, debug_mode)

            # Build request and execute
            response_data = self._build_and_execute_request(
                provider_config, processed_system, processed_user, image_b64_list,
                mask_b64, max_tokens, temperature, top_p, debug_info, debug_mode
            )

            # Store response and handle caching
            context["llm_response"] = response_data
            self._handle_response_caching(use_cache, response_data, debug_info, debug_mode)

            # Log results
            self._log_response_results(response_data, debug_info, debug_mode)

        except Exception as e:
            error_text = str(e)
            if debug_mode:
                debug_info.append(f"✗ Critical error: {error_text}")
            print(f"ERROR executing prompt: {error_text}")
            context["llm_response"] = {"error": {"message": f"Critical error: {error_text}"}}

        # Store debug info if debug mode is enabled
        if debug_mode:
            context["debug_info"] = debug_info
        
        # Return debug info as visible output
        debug_output = "\n".join(debug_info) if debug_mode and debug_info else ""
        
        return (context, debug_output)

    def _parse_template_vars(self, template_vars, debug_info, debug_mode):
        """Parse template variables from JSON string."""
        try:
            return json.loads(template_vars) if template_vars.strip() else {}
        except json.JSONDecodeError as e:
            if debug_mode:
                debug_info.append(f"Warning: Invalid template vars JSON: {e}")
            return {}

    def _process_templates(self, system_prompt, user_prompt, template_variables, debug_info, debug_mode):
        """Process system and user prompts with template variables."""
        processed_system = self._simple_template_render(system_prompt, template_variables)
        processed_user = self._simple_template_render(user_prompt, template_variables)

        if debug_mode:
            debug_info.append(f"Templates processed. System: {len(processed_system)} chars, User: {len(processed_user)} chars")

        return processed_system, processed_user

    def _handle_cache_lookup(self, use_cache, provider_config, processed_system, processed_user,
                            max_tokens, temperature, top_p, images, mask, debug_info, debug_mode):
        """Handle cache lookup and return cached response if found."""
        if not use_cache:
            return None

        cache_key = self._create_cache_key(
            provider_config, processed_system, processed_user,
            max_tokens, temperature, top_p, images, mask
        )

        # Check cache first
        if cache_key in self._cache:
            if debug_mode:
                debug_info.append("✓ Using cached response")
            return self._cache[cache_key]

        # Store cache key for later use
        self._current_cache_key = cache_key
        return None

    def _process_images(self, images, debug_info, debug_mode):
        """Process images to base64 format."""
        image_b64_list = []
        if images is not None:
            try:
                # Use optimized conversion with reasonable defaults
                image_b64_list = tensors_to_base64_list(images, max_size=1024, quality=85)
                if debug_mode:
                    debug_info.append(f"✓ Converted {len(image_b64_list)} image(s) to base64")
            except Exception as e:
                error_msg = f"Failed to process images: {str(e)}"
                if debug_mode:
                    debug_info.append(f"ERROR: {error_msg}")
                return None
        return image_b64_list

    def _process_mask(self, mask, debug_info, debug_mode):
        """Process mask to base64 format."""
        mask_b64 = None
        if mask is not None:
            try:
                mask_b64_list = tensors_to_base64_list(mask, max_size=512, quality=90)
                mask_b64 = mask_b64_list[0] if mask_b64_list else None
                if mask_b64 and debug_mode:
                    debug_info.append("✓ Converted mask to base64")
            except Exception as e:
                if debug_mode:
                    debug_info.append(f"Warning: Failed to convert mask: {e}")
                mask_b64 = None
        return mask_b64

    def _build_and_execute_request(self, provider_config, processed_system, processed_user,
                                  image_b64_list, mask_b64, max_tokens, temperature, top_p,
                                  debug_info, debug_mode):
        """Build and execute the API request."""
        # Build user content (text + images)
        user_content = [{"type": "text", "text": processed_user}]

        # Add images to the user content
        for img_b64 in image_b64_list:
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            }
            user_content.append(image_content)

        # Build messages array
        messages = [
            {"role": "system", "content": processed_system},
            {"role": "user", "content": user_content}
        ]

        # Prepare request parameters
        request_kwargs = {
            "provider": provider_config["provider"],
            "base_url": provider_config["base_url"],
            "api_key": provider_config["api_key"],
            "llm_model": provider_config["llm_model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

        # Add mask if provided (custom extension for some servers)
        if mask_b64:
            request_kwargs["mask"] = mask_b64

        if debug_mode:
            debug_info.append(f"→ Sending request to {provider_config['provider']} at {provider_config['base_url']}")

        # Execute the request
        try:
            response_data = run_async(send_request(**request_kwargs))

            # Extract performance metrics for debug mode
            if debug_mode:
                self._extract_performance_metrics(response_data, debug_info)

            return response_data

        except Exception as e:
            error_text = str(e)
            if debug_mode:
                debug_info.append(f"✗ Request failed: {error_text}")
            print(f"ERROR executing prompt: {error_text}")
            return {"error": {"message": error_text}}

    def _handle_response_caching(self, use_cache, response_data, debug_info, debug_mode):
        """Handle caching of successful responses."""
        if use_cache and hasattr(self, '_current_cache_key') and "error" not in response_data:
            self._cache[self._current_cache_key] = response_data
            self._cleanup_cache()
            if debug_mode:
                debug_info.append("✓ Cached response")

    def _log_response_results(self, response_data, debug_info, debug_mode):
        """Log the results of the API response."""
        if "error" not in response_data:
            choices = response_data.get("choices", [])
            if choices and isinstance(choices[0], dict):
                choice = choices[0]
                message = choice.get("message", {})
                content = message.get("content", "") if isinstance(message, dict) else str(message)
                content_preview = content[:100] if content else "No content"
                if debug_mode:
                    debug_info.append(f"✓ Success: {content_preview}...")
                print(f"SUCCESS: Received response: {content_preview}...")
            else:
                if debug_mode:
                    debug_info.append("✓ Success: Received response")
                print("SUCCESS: Received response")
        else:
            error_msg = response_data.get("error", {})
            if isinstance(error_msg, dict):
                error_text = error_msg.get('message', 'Unknown error')
                if debug_mode:
                    debug_info.append(f"✗ API Error: {error_text}")
                print(f"ERROR in response: {error_text}")
            else:
                if debug_mode:
                    debug_info.append(f"✗ API Error: {error_msg}")
                print(f"ERROR in response: {error_msg}")
