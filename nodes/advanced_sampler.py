"""Advanced VLM Sampler with all heylookitsanllm parameters"""

import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from utils import tensors_to_base64_list
    from shrug_router import send_request
except ImportError:
    # Try relative imports as fallback
    from ..utils import tensors_to_base64_list
    from ..shrug_router import send_request

class AdvancedVLMSampler:
    """
    Advanced VLM sampler with full control over all sampling parameters.
    Exposes all parameters available in heylookitsanllm API.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True, "default": ""}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 32000}),
            },
            "optional": {
                # Images
                "images": ("IMAGE",),
                
                # Core sampling parameters - all defaulting to None to use model defaults
                "temperature": ("FLOAT", {"default": -1, "min": -1, "max": 2.0, "step": 0.01, "display": "number", "tooltip": "-1 = use model default"}),
                "top_p": ("FLOAT", {"default": -1, "min": -1, "max": 1.0, "step": 0.01, "display": "number", "tooltip": "-1 = use model default"}),
                "top_k": ("INT", {"default": -1, "min": -1, "max": 1000, "step": 10, "tooltip": "-1 = use model default"}),
                "min_p": ("FLOAT", {"default": -1, "min": -1, "max": 1.0, "step": 0.01, "display": "number", "tooltip": "-1 = use model default"}),
                
                # Repetition control - default to -1 to use model defaults
                "repetition_penalty": ("FLOAT", {"default": -1, "min": -1, "max": 2.0, "step": 0.01, "display": "number", "tooltip": "-1 = use model default"}),
                "repetition_context_size": ("INT", {"default": -1, "min": -1, "max": 2048, "tooltip": "-1 = use model default"}),
                
                # Generation control
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                
                # Batch processing modes
                "processing_mode": (["conversation", "sequential", "sequential_with_context"], {"default": "conversation"}),
                "return_individual": ("BOOLEAN", {"default": False}),
                
                # Performance options
                "include_performance": ("BOOLEAN", {"default": False}),
                "include_timing": ("BOOLEAN", {"default": False}),
                
                # Streaming (not used in ComfyUI but included for completeness)
                "stream": ("BOOLEAN", {"default": False}),
                
                # Timeout
                "timeout": ("INT", {"default": 300, "min": 30, "max": 1800, "step": 30}),
                
                # Debug
                "debug_mode": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("*", "LIST", "STRING", "FLOAT", "STRING", "SAMPLER_CONFIG")
    RETURN_NAMES = ("context", "responses", "first_response", "avg_time_per_token", "debug_info", "sampler_config")
    FUNCTION = "sample"
    CATEGORY = "VLM/Advanced"
    
    def sample(self, context, system_prompt, user_prompt, max_tokens,
               images=None, temperature=-1, top_p=-1, top_k=-1, min_p=-1,
               repetition_penalty=-1, repetition_context_size=-1, seed=-1,
               processing_mode="conversation", return_individual=False,
               include_performance=False, include_timing=False, stream=False,
               timeout=300, debug_mode=False):
        """
        Execute VLM sampling with advanced parameters.
        """
        debug_info = []
        
        # Get provider config
        provider_config = context.get("provider_config")
        if not provider_config:
            raise ValueError("Provider config required. Connect a VLMProviderConfig node.")
        
        # Process images if provided
        image_b64_list = tensors_to_base64_list(images) if images is not None else []
        
        # Build messages
        messages = self._build_messages(system_prompt, user_prompt, image_b64_list, processing_mode)
        
        # Build request kwargs - only include required parameters
        kwargs = {
            "provider": provider_config["provider"],
            "base_url": provider_config["base_url"],
            "api_key": provider_config["api_key"],
            "llm_model": provider_config["llm_model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
            "include_performance": include_performance,
            "timeout": timeout
        }
        
        # Add optional parameters only if explicitly set (not -1)
        if temperature >= 0:
            kwargs["temperature"] = temperature
        if top_p >= 0:
            kwargs["top_p"] = top_p
        if top_k >= 0:
            kwargs["top_k"] = top_k
        if min_p >= 0:
            kwargs["min_p"] = min_p
        if repetition_penalty >= 0:
            kwargs["repetition_penalty"] = repetition_penalty
        if repetition_context_size >= 0:
            kwargs["repetition_context_size"] = repetition_context_size
        if seed >= 0:
            kwargs["seed"] = seed
        if processing_mode != "conversation":
            kwargs["processing_mode"] = processing_mode
        if return_individual:
            kwargs["return_individual"] = return_individual
        if include_timing:
            kwargs["include_timing"] = include_timing
        
        if debug_mode:
            params_used = []
            if temperature >= 0: params_used.append(f"temp={temperature}")
            if top_p >= 0: params_used.append(f"top_p={top_p}")
            if top_k >= 0: params_used.append(f"top_k={top_k}")
            if min_p >= 0: params_used.append(f"min_p={min_p}")
            if repetition_penalty >= 0: params_used.append(f"rep_penalty={repetition_penalty}")
            if repetition_context_size >= 0: params_used.append(f"rep_context={repetition_context_size}")
            if seed >= 0: params_used.append(f"seed={seed}")
            
            if params_used:
                debug_info.append(f"Custom params: {', '.join(params_used)}")
            else:
                debug_info.append("Using all model default parameters")
            debug_info.append(f"Mode: {processing_mode}")
        
        # Make request
        try:
            response = send_request(**kwargs)
            
            # Extract responses
            responses = []
            avg_time_per_token = 0.0
            
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                responses = [f"Error: {error_msg}"]
                if debug_mode:
                    debug_info.append(f"Request failed: {error_msg}")
            else:
                # Handle different response formats
                if "choices" in response:
                    # Standard format
                    for choice in response["choices"]:
                        content = choice.get("message", {}).get("content", "")
                        responses.append(content)
                elif "completions" in response:
                    # Batch format
                    for completion in response["completions"]:
                        if isinstance(completion, dict) and "choices" in completion:
                            content = completion["choices"][0].get("message", {}).get("content", "")
                            responses.append(content)
                
                # Extract performance metrics if available
                if include_performance and "performance" in response:
                    perf = response["performance"]
                    avg_time_per_token = perf.get("avg_time_per_token", 0.0)
                    if debug_mode:
                        debug_info.append(f"Performance: {perf.get('total_time', 0):.2f}s total")
                        debug_info.append(f"Tokens/sec: {perf.get('tokens_per_second', 0):.2f}")
            
            # Update context
            context["llm_response"] = response
            context["llm_responses"] = responses
            
            # Build sampler config with only non-default values
            sampler_config = {
                "processing_mode": processing_mode,
                "return_individual": return_individual,
                "include_performance": include_performance,
                "include_timing": include_timing,
                "timeout": timeout
            }
            
            # Add optional parameters only if explicitly set
            if temperature >= 0: sampler_config["temperature"] = temperature
            if top_p >= 0: sampler_config["top_p"] = top_p
            if top_k >= 0: sampler_config["top_k"] = top_k
            if min_p >= 0: sampler_config["min_p"] = min_p
            if repetition_penalty >= 0: sampler_config["repetition_penalty"] = repetition_penalty
            if repetition_context_size >= 0: sampler_config["repetition_context_size"] = repetition_context_size
            if seed >= 0: sampler_config["seed"] = seed
            
            context["sampling_params"] = sampler_config
            
            first_response = responses[0] if responses else ""
            
            if debug_mode:
                debug_info.append(f"Generated {len(responses)} response(s)")
            
            return (context, responses, first_response, avg_time_per_token, "\n".join(debug_info), sampler_config)
            
        except Exception as e:
            error_msg = f"Sampling error: {str(e)}"
            if debug_mode:
                import traceback
                debug_info.append(traceback.format_exc())
            return (context, [error_msg], error_msg, 0.0, "\n".join(debug_info), {})
    
    def _build_messages(self, system_prompt, user_prompt, images, processing_mode):
        """Build messages based on processing mode"""
        if processing_mode == "sequential" and len(images) > 1:
            # Each image gets its own conversation
            all_messages = []
            for img_b64 in images:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]}
                ]
                all_messages.append(messages)
            return all_messages
        else:
            # Single conversation with all images
            user_content = [{"type": "text", "text": user_prompt}]
            for img_b64 in images:
                user_content.append({
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                })
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]


NODE_CLASS_MAPPINGS = {
    "AdvancedVLMSampler": AdvancedVLMSampler,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AdvancedVLMSampler": "Advanced VLM Sampler",
}