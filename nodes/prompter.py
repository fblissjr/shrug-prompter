# In shrug-prompter/nodes/prompter.py
try:
    from ..utils import tensors_to_base64_list, run_async
    from ..shrug_router import send_request
except ImportError:
    from utils import tensors_to_base64_list, run_async
    from shrug_router import send_request

import hashlib
import json

class ShrugPrompter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),
                "system_prompt": ("STRING", {"multiline": True, "default": "You are a helpful assistant."}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_tokens": ("INT", {"default": 1024, "min": 1, "max": 8192}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0}),
            },
            "optional": {
                "images": ("IMAGE",),
                "mask": ("MASK",),
                # WHY: This input allows the behavior defined in the template's metadata
                # to be passed through the workflow context.
                "metadata": ("STRING", {"default": "{}"}),
                "template_vars": ("STRING", {"multiline": True, "default": "{}"}),
                "use_cache": ("BOOLEAN", {"default": True}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("*", "STRING")
    RETURN_NAMES = ("context", "debug_info")
    FUNCTION = "execute_prompt"
    CATEGORY = "Shrug Nodes/Logic"
    # WHY: The debug output is now a list so it can be expanded and viewed
    # inside a loop alongside the per-item output from the parser.
    OUTPUT_IS_LIST = (False, True)

    def __init__(self):
        self._cache = {}
        self._cache_max_size = 50

    def execute_prompt(self, context, system_prompt, user_prompt, max_tokens, temperature, top_p,
                          images=None, mask=None, metadata="{}", template_vars="{}", use_cache=True, debug_mode=False):

        debug_info = []
        # WHY: The metadata is added to the context here. The Prompter doesn't need
        # to know what's in it; its job is simply to pass it along for the Parser.
        context["vlm_metadata"] = metadata

        try:
            provider_config = context.get("provider_config")
            if not provider_config: raise ValueError("A `provider_config` from a ShrugProviderSelector is required.")
            if debug_mode: debug_info.append(f"Provider: {provider_config.get('provider')}, Model: {provider_config.get('llm_model')}")

            template_variables = self._parse_template_vars(template_vars, debug_info, debug_mode)
            processed_system = self._simple_template_render(system_prompt, template_variables)
            processed_user = self._simple_template_render(user_prompt, template_variables)

            cache_key = self._create_cache_key(provider_config, processed_system, processed_user, max_tokens, temperature, top_p, images, mask)
            if use_cache and cache_key in self._cache:
                if debug_mode: debug_info.append("✓ Using cached VLM response")
                context["llm_response"] = self._cache[cache_key]
                return (context, [ "\n".join(debug_info) ])

            image_b64_list = self._process_images(images, debug_info, debug_mode)
            mask_b64 = self._process_mask(mask, debug_info, debug_mode)

            response_data = self._build_and_execute_request(provider_config, processed_system, processed_user, image_b64_list, mask_b64, max_tokens, temperature, top_p, debug_info, debug_mode)

            context["llm_response"] = response_data
            if use_cache and "error" not in response_data:
                self._cache[cache_key] = response_data
                self._cleanup_cache()
                if debug_mode: debug_info.append("✓ Cached new VLM response")

            self._log_response_results(response_data, debug_info, debug_mode)

        except Exception as e:
            error_text = str(e)
            if debug_mode: debug_info.append(f"✗ CRITICAL PROMPTER ERROR: {error_text}")
            context["llm_response"] = {"error": {"message": f"Critical error: {error_text}"}}

        return (context, [ "\n".join(debug_info) ])

    # All helper methods remain the same as before.
    def _simple_template_render(self, template: str, variables: dict) -> str:
        if not variables: return template
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    def _parse_template_vars(self, template_vars: str, debug_info: list, debug_mode: bool) -> dict:
        try:
            return json.loads(template_vars) if template_vars.strip() else {}
        except json.JSONDecodeError as e:
            if debug_mode: debug_info.append(f"Warning: Invalid template_vars JSON: {e}")
            return {}

    def _create_cache_key(self, provider_config, system_prompt, user_prompt, max_tokens, temperature, top_p, images, mask) -> str:
        cache_data = { "provider": provider_config.get("provider"), "model": provider_config.get("llm_model"), "system": system_prompt, "user": user_prompt, "max_tokens": max_tokens, "temperature": temperature, "top_p": top_p, "images_shape": str(images.shape) if images is not None else "None", "mask_shape": str(mask.shape) if mask is not None else "None" }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    def _cleanup_cache(self):
        if len(self._cache) > self._cache_max_size:
            keys_to_remove = list(self._cache.keys())[:len(self._cache) - self._cache_max_size]
            for key in keys_to_remove: del self._cache[key]

    def _process_images(self, images, debug_info: list, debug_mode: bool) -> list:
        if images is None: return []
        try:
            image_b64_list = tensors_to_base64_list(images)
            if debug_mode: debug_info.append(f"✓ Converted {len(image_b64_list)} image(s) to base64")
            return image_b64_list
        except Exception as e:
            if debug_mode: debug_info.append(f"ERROR processing images: {e}")
            return []

    def _process_mask(self, mask, debug_info: list, debug_mode: bool):
        if mask is None: return None
        try:
            mask_b64_list = tensors_to_base64_list(mask)
            if mask_b64_list and debug_mode: debug_info.append("✓ Converted mask to base64")
            return mask_b64_list[0] if mask_b64_list else None
        except Exception as e:
            if debug_mode: debug_info.append(f"Warning: Failed to convert mask: {e}")
            return None

    def _build_and_execute_request(self, provider_config, system, user, images, mask, max_tokens, temp, top_p, debug_info, debug_mode):
        user_content = [{"type": "text", "text": user}]
        for img_b64 in images:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user_content}]
        kwargs = {"provider": provider_config["provider"], "base_url": provider_config["base_url"], "api_key": provider_config["api_key"], "llm_model": provider_config["llm_model"], "messages": messages, "max_tokens": max_tokens, "temperature": temp, "top_p": top_p, "mask": mask}
        if debug_mode: debug_info.append(f"→ Sending request to {provider_config['provider']}...")
        try:
            response = run_async(send_request(**kwargs))
            if debug_mode: self._extract_performance_metrics(response, debug_info)
            return response
        except Exception as e:
            if debug_mode: debug_info.append(f"✗ Request failed: {e}")
            return {"error": {"message": str(e)}}

    def _log_response_results(self, response, debug_info, debug_mode):
        if "error" in response:
            if debug_mode: debug_info.append(f"✗ API Error: {response['error'].get('message', 'Unknown')}")
        elif response.get("choices"):
            content = response["choices"][0].get("message", {}).get("content", "No content")
            if debug_mode: debug_info.append(f"✓ Success: Response received ({len(content)} chars)")
        else:
            if debug_mode: debug_info.append("✓ Success: Received response (no choices field)")

    def _extract_performance_metrics(self, response, debug_info):
        if isinstance(response, dict) and 'eval_count' in response and 'eval_duration' in response and response['eval_duration'] > 0:
            tps = response['eval_count'] / (response['eval_duration'] / 1e9)
            debug_info.append(f"Performance: {tps:.1f} tok/s")
