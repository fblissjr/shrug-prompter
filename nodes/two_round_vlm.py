# Two-Round VLM Processing for shrug-prompter
# Round 1: Any VLM for observation
# Round 2: Qwen2.5 for style rewriting (Alibaba family compatibility with WAN)

import sys
import os
import json
import hashlib
from typing import Dict, Any, Optional, Tuple, List

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

class TwoRoundVLMPrompter:
    """
    Two-round VLM processing node:
    - Round 1: Any VLM model analyzes the image (multimodal)
    - Round 2: Qwen2.5 rewrites the output for target use case (text-only)
    
    This enables using specialized models for each task:
    - Best vision model for observation (e.g., GPT-4V, Claude, Gemini)
    - Qwen2.5 for WAN-compatible prompt rewriting (same Alibaba family)
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Round 1 - Observation
                "round1_context": ("VLM_CONTEXT",),
                "round1_system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a highly observant assistant. Describe what you see in extreme detail."
                }),
                "round1_user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "Describe this image in comprehensive detail, including all visual elements, colors, composition, and any notable features."
                }),
                
                # Round 2 - Rewriting
                "round2_context": ("VLM_CONTEXT",),
                "round2_system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are an expert prompt engineer for WAN VACE video generation models."
                }),
                "round2_user_prompt": ("STRING", {
                    "multiline": True,
                    "default": "Rewrite the following description as a cinematic prompt suitable for video generation. Focus on movement, atmosphere, and visual style."
                }),
                
                # Shared parameters
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 32000}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "images": ("IMAGE",),
                "round1_template": ("STRING", {"multiline": True}),
                "round2_template": ("STRING", {"multiline": True}),
                "pass_observation": ("BOOLEAN", {"default": True, "description": "Pass Round 1 output to Round 2"}),
                "batch_mode": ("BOOLEAN", {"default": False}),
                "debug_mode": ("BOOLEAN", {"default": False}),
                "response_cleanup": ("STRING", {
                    "default": "standard",
                    "choices": ["none", "basic", "standard", "strict"]
                }),
                # Image preprocessing for Round 1
                "resize_mode": ("STRING", {
                    "default": "none",
                    "choices": ["none", "max", "width", "height", "exact"]
                }),
                "resize_value": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "image_quality": ("INT", {"default": 85, "min": 1, "max": 100}),
            }
        }
    
    RETURN_TYPES = ("VLM_CONTEXT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("context", "final_prompt", "round1_observation", "debug_info")
    FUNCTION = "process_two_rounds"
    CATEGORY = "VLM/Advanced"
    
    def __init__(self):
        self.text_cleaner = TextCleanupNode() if TextCleanupNode else None
    
    def process_two_rounds(self, round1_context, round1_system_prompt, round1_user_prompt,
                          round2_context, round2_system_prompt, round2_user_prompt,
                          max_tokens, temperature, top_p,
                          images=None, round1_template=None, round2_template=None,
                          pass_observation=True, batch_mode=False, debug_mode=False,
                          response_cleanup="standard", resize_mode="none", 
                          resize_value=512, image_quality=85):
        
        debug_output = []
        
        # Round 1: Visual Observation (Multimodal)
        if debug_mode:
            debug_output.append("=== ROUND 1: OBSERVATION ===")
            debug_output.append(f"Provider: {round1_context.get('model', 'Unknown')}")
        
        # Apply template to Round 1 if provided
        if round1_template:
            round1_user_prompt = self._apply_template(round1_template, round1_user_prompt)
        
        # Process images if batch mode
        if batch_mode and images is not None and len(images) > 1:
            round1_responses = self._process_batch_round1(
                round1_context, images, round1_system_prompt, round1_user_prompt,
                max_tokens, temperature, top_p, resize_mode, resize_value, image_quality, debug_mode
            )
            round1_observation = "\n---\n".join(round1_responses)
        else:
            # Single image processing
            round1_observation = self._process_single_round1(
                round1_context, images, round1_system_prompt, round1_user_prompt,
                max_tokens, temperature, top_p, resize_mode, resize_value, image_quality, debug_mode
            )
        
        if debug_mode:
            debug_output.append(f"Round 1 Response Length: {len(round1_observation)} chars")
            debug_output.append(f"Round 1 Output:\n{round1_observation[:500]}...")
        
        # Clean Round 1 response if needed
        if response_cleanup != "none" and self.text_cleaner:
            round1_observation = self._cleanup_response(round1_observation, response_cleanup)
        
        # Round 2: Style Rewriting (Text-only with Qwen2.5)
        if debug_mode:
            debug_output.append("\n=== ROUND 2: REWRITING ===")
            debug_output.append(f"Provider: {round2_context.get('model', 'Unknown')}")
            debug_output.append(f"Pass observation: {pass_observation}")
        
        # Prepare Round 2 prompt
        if pass_observation:
            # Inject Round 1 observation into Round 2 prompt
            round2_full_prompt = f"{round2_user_prompt}\n\nOriginal description:\n{round1_observation}"
        else:
            round2_full_prompt = round2_user_prompt
        
        # Apply template to Round 2 if provided
        if round2_template:
            round2_full_prompt = self._apply_template(round2_template, round2_full_prompt)
        
        # Round 2 is text-only (no images)
        final_prompt = self._process_round2(
            round2_context, round2_system_prompt, round2_full_prompt,
            max_tokens, temperature, top_p, debug_mode
        )
        
        if debug_mode:
            debug_output.append(f"Round 2 Response Length: {len(final_prompt)} chars")
            debug_output.append(f"Round 2 Output:\n{final_prompt[:500]}...")
        
        # Clean final response
        if response_cleanup != "none" and self.text_cleaner:
            final_prompt = self._cleanup_response(final_prompt, response_cleanup)
        
        # Update context with both rounds info
        updated_context = round2_context.copy()
        updated_context['two_round_processing'] = {
            'round1_model': round1_context.get('model', 'Unknown'),
            'round2_model': round2_context.get('model', 'Unknown'),
            'observation_length': len(round1_observation),
            'final_length': len(final_prompt)
        }
        
        debug_info = "\n".join(debug_output) if debug_mode else ""
        
        return (updated_context, final_prompt, round1_observation, debug_info)
    
    def _process_single_round1(self, context, images, system_prompt, user_prompt,
                               max_tokens, temperature, top_p, resize_mode, 
                               resize_value, image_quality, debug_mode):
        """Process Round 1 with visual observation"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Add images if provided
        if images is not None:
            # Check capabilities for optimal processing
            if CapabilityDetector:
                detector = CapabilityDetector(context.get('base_url', 'http://localhost:8080'))
                capabilities = detector.detect_capabilities()
            else:
                capabilities = {}
            
            # Process images based on capabilities
            if capabilities.get('multipart_support'):
                image_data = tensors_to_raw_bytes_list(images)
                messages[-1]["images"] = image_data
            else:
                image_data = tensors_to_base64_list(images)
                messages[-1]["images"] = image_data
            
            # Add resize parameters if server supports it
            if capabilities.get('resize_support') and resize_mode != "none":
                messages[-1]["resize_mode"] = resize_mode
                messages[-1]["resize_value"] = resize_value
                messages[-1]["image_quality"] = image_quality
        
        response = send_request(
            context=context,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        
        return response.get('content', '')
    
    def _process_batch_round1(self, context, images, system_prompt, user_prompt,
                             max_tokens, temperature, top_p, resize_mode,
                             resize_value, image_quality, debug_mode):
        """Process multiple images in Round 1"""
        responses = []
        for i, image in enumerate(images):
            response = self._process_single_round1(
                context, [image], system_prompt, user_prompt,
                max_tokens, temperature, top_p, resize_mode,
                resize_value, image_quality, debug_mode
            )
            responses.append(f"Image {i+1}:\n{response}")
        return responses
    
    def _process_round2(self, context, system_prompt, user_prompt,
                       max_tokens, temperature, top_p, debug_mode):
        """Process Round 2 text-only rewriting"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = send_request(
            context=context,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        
        return response.get('content', '')
    
    def _apply_template(self, template, prompt):
        """Apply template variables to prompt"""
        try:
            # Simple template substitution
            return template.format(prompt=prompt)
        except:
            return prompt
    
    def _cleanup_response(self, text, mode):
        """Clean up response text"""
        if not self.text_cleaner:
            return text
        
        operations = {
            "basic": "trim",
            "standard": "trim,unicode,newlines",
            "strict": "trim,unicode,newlines,collapse,quotes"
        }.get(mode, "trim")
        
        cleaned, _ = self.text_cleaner.cleanup_text(text, operations)
        return cleaned


class VLMStyleRewriter:
    """
    Specialized node for style rewriting with Qwen2.5 or other text models.
    Takes existing text and rewrites it for specific use cases.
    Perfect for the second round of two-round processing.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("VLM_CONTEXT",),
                "input_text": ("STRING", {"multiline": True}),
                "rewrite_instruction": ("STRING", {
                    "multiline": True,
                    "default": "Rewrite this as a cinematic video generation prompt"
                }),
                "style": ("STRING", {
                    "default": "cinematic",
                    "choices": ["cinematic", "technical", "narrative", "artistic", "documentary", "custom"]
                }),
                "max_tokens": ("INT", {"default": 256, "min": 1, "max": 4096}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are an expert at rewriting text for specific purposes while maintaining accuracy."
                }),
                "trigger_word": ("STRING", {"default": ""}),
                "avoid_terms": ("STRING", {"default": ""}),
                "response_cleanup": ("STRING", {
                    "default": "standard",
                    "choices": ["none", "basic", "standard", "strict"]
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "VLM_CONTEXT")
    RETURN_NAMES = ("rewritten_text", "context")
    FUNCTION = "rewrite_style"
    CATEGORY = "VLM/Text"
    
    def __init__(self):
        self.text_cleaner = TextCleanupNode() if TextCleanupNode else None
        self.style_prompts = {
            "cinematic": "Focus on camera movements, lighting, atmosphere, and visual drama",
            "technical": "Use precise technical terminology and structured descriptions",
            "narrative": "Create a story-like flow with character focus and emotional beats",
            "artistic": "Emphasize aesthetic qualities, composition, and artistic style",
            "documentary": "Provide factual, observational descriptions with context",
            "custom": ""  # Use user's instruction as-is
        }
    
    def rewrite_style(self, context, input_text, rewrite_instruction, style,
                     max_tokens, temperature, system_prompt=None,
                     trigger_word="", avoid_terms="", response_cleanup="standard"):
        
        # Build the rewriting prompt
        style_guidance = self.style_prompts.get(style, "")
        
        full_instruction = rewrite_instruction
        if style_guidance and style != "custom":
            full_instruction += f"\n\nStyle guidance: {style_guidance}"
        
        if trigger_word:
            full_instruction += f"\n\nUse '{trigger_word}' as the main subject identifier."
        
        if avoid_terms:
            full_instruction += f"\n\nAvoid these terms: {avoid_terms}"
        
        user_prompt = f"{full_instruction}\n\nText to rewrite:\n{input_text}"
        
        # Use provided system prompt or default
        if not system_prompt:
            system_prompt = "You are an expert at rewriting text for specific purposes while maintaining accuracy."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = send_request(
            context=context,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9  # Fixed top_p for consistency
        )
        
        rewritten = response.get('content', '')
        
        # Clean up response if requested
        if response_cleanup != "none" and self.text_cleaner:
            operations = {
                "basic": "trim",
                "standard": "trim,unicode,newlines",
                "strict": "trim,unicode,newlines,collapse,quotes"
            }.get(response_cleanup, "trim")
            
            rewritten, _ = self.text_cleaner.cleanup_text(rewritten, operations)
        
        return (rewritten, context)


class DualProviderConfig:
    """
    Configure two different VLM providers for two-round processing.
    Enables using different models for observation vs rewriting.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Round 1 Provider (Observation)
                "round1_base_url": ("STRING", {
                    "default": "http://localhost:8080",
                    "display": "text"
                }),
                "round1_model": ("STRING", {
                    "default": "gpt-4-vision-preview",
                    "display": "text"
                }),
                "round1_api_key": ("STRING", {
                    "default": "",
                    "display": "password"
                }),
                
                # Round 2 Provider (Rewriting)
                "round2_base_url": ("STRING", {
                    "default": "http://localhost:8080",
                    "display": "text"
                }),
                "round2_model": ("STRING", {
                    "default": "qwen2.5-72b-instruct",
                    "display": "text"
                }),
                "round2_api_key": ("STRING", {
                    "default": "",
                    "display": "password"
                }),
            },
            "optional": {
                "round1_api_format": ("STRING", {
                    "default": "openai",
                    "choices": ["openai", "ollama", "anthropic"]
                }),
                "round2_api_format": ("STRING", {
                    "default": "openai",
                    "choices": ["openai", "ollama", "anthropic"]
                }),
            }
        }
    
    RETURN_TYPES = ("VLM_CONTEXT", "VLM_CONTEXT")
    RETURN_NAMES = ("round1_context", "round2_context")
    FUNCTION = "create_dual_contexts"
    CATEGORY = "VLM/Config"
    
    def create_dual_contexts(self, round1_base_url, round1_model, round1_api_key,
                            round2_base_url, round2_model, round2_api_key,
                            round1_api_format="openai", round2_api_format="openai"):
        
        round1_context = {
            "base_url": round1_base_url,
            "model": round1_model,
            "api_key": round1_api_key if round1_api_key else None,
            "api_format": round1_api_format,
            "round": "observation"
        }
        
        round2_context = {
            "base_url": round2_base_url,
            "model": round2_model,
            "api_key": round2_api_key if round2_api_key else None,
            "api_format": round2_api_format,
            "round": "rewriting"
        }
        
        return (round1_context, round2_context)


# Node registration
NODE_CLASS_MAPPINGS = {
    "TwoRoundVLMPrompter": TwoRoundVLMPrompter,
    "VLMStyleRewriter": VLMStyleRewriter,
    "DualProviderConfig": DualProviderConfig,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TwoRoundVLMPrompter": "Two-Round VLM Prompter",
    "VLMStyleRewriter": "VLM Style Rewriter",
    "DualProviderConfig": "Dual Provider Config",
}