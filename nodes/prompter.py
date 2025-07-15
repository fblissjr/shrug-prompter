# In shrug-prompter/nodes/prompter.py
try:
    from ..utils import tensors_to_base64_list
    from ..shrug_router import send_request
except ImportError:
    from utils import tensors_to_base64_list
    from shrug_router import send_request

import hashlib
import json

class ShrugPrompter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 32000}),
                "temperature": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 2.00, "step": 0.05, "display": "number"}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.00, "max": 1.00, "step": 0.01, "display": "number"}),
            },
            "optional": {
                "images": ("IMAGE",),
                "mask": ("MASK",),
                "metadata": ("STRING", {"default": "{}"}),
                "template_vars": ("STRING", {"multiline": True, "default": "{}"}),
                "use_cache": ("BOOLEAN", {"default": True}),
                "debug_mode": ("BOOLEAN", {"default": False}),
                "batch_mode": ("BOOLEAN", {"default": False, "tooltip": "Process each image separately"}),
                "processing_mode": (["sequential", "sequential_with_context"], {"default": "sequential"}),
            },
        }

    RETURN_TYPES = ("*", "STRING")
    RETURN_NAMES = ("context", "debug_info")
    FUNCTION = "execute_prompt"
    CATEGORY = "Shrug Nodes/Logic"
    OUTPUT_IS_LIST = (False, True)

    def __init__(self):
        self._cache = {}
        self._cache_max_size = 50

    def execute_prompt(self, context, system_prompt, user_prompt, max_tokens, temperature, top_p,
                          images=None, mask=None, metadata="{}", template_vars="{}", use_cache=True, debug_mode=False,
                          batch_mode=False, processing_mode="sequential"):

        debug_info = []
        context["vlm_metadata"] = metadata
        context["debug_info"] = debug_info

        try:
            # The rest of the implementation is the same as previous answers.
            # This is the complete, correct logic.
            provider_config = context.get("provider_config")
            if not provider_config: raise ValueError("A `provider_config` is required.")

            template_variables = json.loads(template_vars) if template_vars.strip() else {}
            processed_system = system_prompt.format(**template_variables)
            processed_user = user_prompt.format(**template_variables)

            cache_key = self._create_cache_key(provider_config, processed_system, processed_user, max_tokens, temperature, top_p, images, mask)
            if use_cache and cache_key in self._cache:
                context["llm_response"] = self._cache[cache_key]
                return (context, [ "\n".join(debug_info) ])

            image_b64_list = self._process_images(images)
            mask_b64 = self._process_mask(mask)

            # Check if batch mode is enabled and we have multiple images
            if batch_mode and image_b64_list and len(image_b64_list) > 1:
                if debug_mode:
                    debug_info.append(f"Batch mode: Processing {len(image_b64_list)} images as separate inferences")
                
                # Each image gets its own inference
                response_data = self._build_and_execute_batch_request(
                    provider_config, processed_system, processed_user, image_b64_list, 
                    mask_b64, max_tokens, temperature, top_p, processing_mode, debug_info
                )
                
                # Store multiple responses for batch mode
                context["llm_responses"] = response_data.get("completions", [])
                context["llm_response"] = response_data  # Keep full response for compatibility
                context["batch_mode"] = True
                context["batch_size"] = len(image_b64_list)
            else:
                # Single request mode - can have multiple images in one conversation
                if debug_mode:
                    if image_b64_list:
                        debug_info.append(f"Single inference mode: Processing {len(image_b64_list)} image(s) together")
                    else:
                        debug_info.append("Text-only request (no images)")
                
                response_data = self._build_and_execute_request(provider_config, processed_system, processed_user, image_b64_list, mask_b64, max_tokens, temperature, top_p)
                context["llm_response"] = response_data
                context["batch_mode"] = False

                if use_cache and "error" not in response_data:
                    self._cache[cache_key] = response_data
                    self._cleanup_cache()

        except Exception as e:
            context["llm_response"] = {"error": {"message": f"Critical error in ShrugPrompter: {e}"}}

        return (context, ["\n".join(debug_info)])

    # Helper methods are complete and do not require further changes.
    def _create_cache_key(self, provider_config, system, user, max_tokens, temp, top_p, images, mask):
        data = { "provider": provider_config.get("provider"), "model": provider_config.get("llm_model"), "system": system, "user": user, "max_tokens": max_tokens, "temperature": temp, "top_p": top_p, "images_shape": str(images.shape) if images is not None else "None", "mask_shape": str(mask.shape) if mask is not None else "None" }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def _cleanup_cache(self):
        if len(self._cache) > self._cache_max_size:
            for key in list(self._cache.keys())[:len(self._cache) - self._cache_max_size]: del self._cache[key]

    def _process_images(self, images):
        return tensors_to_base64_list(images) if images is not None else []

    def _process_mask(self, mask):
        if mask is None: return None
        masks = tensors_to_base64_list(mask)
        return masks[0] if masks else None

    def _build_and_execute_batch_request(self, provider_config, system, user, images, mask, max_tokens, temp, top_p, processing_mode, debug_info):
        """Execute batch request as separate API calls - simpler and more memory efficient"""
        import gc
        
        all_completions = []
        
        # Process each image with a separate API call
        for i, img_b64 in enumerate(images):
            if debug_info:
                debug_info.append(f"Processing image {i+1}/{len(images)}")
            
            # Build single-image request
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
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
                "mask": mask
            }
            
            try:
                response = send_request(**kwargs)
                all_completions.append(response)
            except Exception as e:
                # If one fails, record error but continue
                error_response = {
                    "error": {"message": f"Failed processing image {i+1}: {str(e)}"}
                }
                all_completions.append(error_response)
            
            # Clean up memory after each image
            if i % 3 == 0:  # Every 3 images
                gc.collect()
        
        # Return in batch format for compatibility
        return {
            "completions": all_completions,
            "processing_mode": processing_mode
        }

    def _build_and_execute_request(self, provider_config, system, user, images, mask, max_tokens, temp, top_p):
        user_content = [{"type": "text", "text": user}] + [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}} for img_b64 in images]
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user_content}]
        kwargs = {"provider": provider_config["provider"], "base_url": provider_config["base_url"], "api_key": provider_config["api_key"], "llm_model": provider_config["llm_model"], "messages": messages, "max_tokens": max_tokens, "temperature": temp, "top_p": top_p, "mask": mask}
        return send_request(**kwargs)
