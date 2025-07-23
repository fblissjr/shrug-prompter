"""
Loop-compatible nodes for complex workflows like almost.json.
These nodes maintain state across ForLoop iterations and handle accumulation properly.
"""

import torch
import weakref
from typing import Dict, Any, List, Optional, Union

from .core_vlm_nodes import memory_tracker


class LoopAwareVLMAccumulator:
    """
    VLM accumulator that works inside ForLoop structures.
    Maintains state across iterations and handles batch/single responses.
    Compatible with the original BatchVLMAccumulator behavior.
    """

    # Class-level storage for accumulator state
    _accumulators = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),  # Accept any context type
                "accumulator_id": ("STRING", {"default": "default"}),
            },
            "optional": {
                "reset": ("BOOLEAN", {"default": False}),
                "extract_mode": (["all", "responses_only", "first_response"], {"default": "responses_only"}),
                "clear_all": ("BOOLEAN", {"default": False, "tooltip": "Clear ALL accumulators across all IDs"}),
            }
        }

    RETURN_TYPES = ("ACCUMULATION", "LIST", "INT", "STRING")
    RETURN_NAMES = ("accumulator", "responses", "total_count", "debug_info")
    OUTPUT_IS_LIST = (False, True, False, False)
    FUNCTION = "accumulate_vlm"
    CATEGORY = "VLM/Loop"

    @classmethod
    def clear_all_accumulators(cls):
        """Clear all accumulated data across all IDs"""
        count = len(cls._accumulators)
        cls._accumulators.clear()
        return count
    
    def accumulate_vlm(self, context, accumulator_id="default", reset=False, extract_mode="responses_only", clear_all=False):
        """Accumulate VLM responses, handling both single and batch modes."""
        
        # Clear all accumulators if requested
        if clear_all:
            count = self.clear_all_accumulators()
            print(f"[LoopAwareVLMAccumulator] Cleared {count} accumulators")

        # Initialize or reset accumulator
        if reset or accumulator_id not in self._accumulators:
            self._accumulators[accumulator_id] = {
                "contexts": [],
                "responses": [],
                "metadata": {
                    "total_single": 0,
                    "total_batch": 0,
                    "total_responses": 0
                }
            }

        acc = self._accumulators[accumulator_id]
        responses_to_add = []
        debug_lines = []

        # Handle different context types
        if isinstance(context, dict):
            # Check for cleaned responses first (from ShrugPrompter with cleanup)
            if "cleaned_responses" in context and isinstance(context["cleaned_responses"], list):
                # Use pre-cleaned responses
                batch_responses = context["cleaned_responses"]
                debug_lines.append(f"Using cleaned responses: {len(batch_responses)} responses")
                
                for response in batch_responses:
                    if extract_mode == "responses_only":
                        responses_to_add.append(response)
                    elif extract_mode == "first_response" and len(responses_to_add) == 0:
                        responses_to_add.append(response)
                    else:  # all
                        responses_to_add.append(response)
                
                acc["metadata"]["total_single"] += 1
                acc["metadata"]["total_responses"] += len(batch_responses)
                
            # Check for VLMPrompter output format
            elif "responses" in context and isinstance(context["responses"], list):
                # New VLMPrompter format
                batch_responses = context["responses"]
                debug_lines.append(f"VLMPrompter format: {len(batch_responses)} responses")

                for response in batch_responses:
                    if extract_mode == "responses_only":
                        responses_to_add.append(response)
                    elif extract_mode == "first_response" and len(responses_to_add) == 0:
                        responses_to_add.append(response)
                    else:  # all
                        responses_to_add.append(response)

                acc["metadata"]["total_batch"] += 1
                acc["metadata"]["total_responses"] += len(batch_responses)

            # Check for original ShrugPrompter format
            elif context.get("batch_mode", False) and "llm_responses" in context:
                # Original batch mode
                batch_responses = context.get("llm_responses", [])
                debug_lines.append(f"ShrugPrompter batch: {len(batch_responses)} responses")

                for i, response in enumerate(batch_responses):
                    if extract_mode == "responses_only":
                        text = self._extract_text_from_response(response)
                        responses_to_add.append(text)
                    elif extract_mode == "first_response" and i == 0:
                        text = self._extract_text_from_response(response)
                        responses_to_add.append(text)
                        break
                    else:  # all
                        responses_to_add.append(response)

                acc["metadata"]["total_batch"] += 1
                acc["metadata"]["total_responses"] += len(batch_responses)

            else:
                # Single response mode
                response = context.get("llm_response") or context.get("response")
                if response:
                    debug_lines.append("Single response mode")

                    if extract_mode == "responses_only" or extract_mode == "first_response":
                        text = self._extract_text_from_response(response)
                        responses_to_add.append(text)
                    else:  # all
                        responses_to_add.append(response)

                    acc["metadata"]["total_single"] += 1
                    acc["metadata"]["total_responses"] += 1

        # Add to accumulator
        acc["contexts"].append(context)
        acc["responses"].extend(responses_to_add)

        # Build debug info
        debug_info = "\n".join([
            f"Accumulator ID: {accumulator_id}",
            f"Total contexts: {len(acc['contexts'])}",
            f"Total responses: {len(acc['responses'])}",
            f"Single mode calls: {acc['metadata']['total_single']}",
            f"Batch mode calls: {acc['metadata']['total_batch']}",
            *debug_lines
        ])

        # Create output accumulator
        output_acc = {
            "contexts": acc["contexts"].copy(),
            "responses": acc["responses"].copy(),
            "metadata": acc["metadata"].copy()
        }

        # Clean up periodically
        if len(acc["contexts"]) % 10 == 0:
            memory_tracker.cleanup()
            
        # More aggressive cleanup - limit to 3 accumulators
        if len(self._accumulators) > 3:
            # Keep only the 2 most recently used
            sorted_ids = sorted(self._accumulators.keys(), 
                              key=lambda k: len(self._accumulators[k]["contexts"]), 
                              reverse=True)
            removed_count = 0
            for old_id in sorted_ids[2:]:
                if old_id != accumulator_id:  # Don't remove current one
                    del self._accumulators[old_id]
                    removed_count += 1
            if removed_count > 0:
                print(f"[LoopAwareVLMAccumulator] Cleaned up {removed_count} old accumulators")

        return (output_acc, acc["responses"], len(acc["responses"]), debug_info)

    def _extract_text_from_response(self, response: Any) -> str:
        """Extract text content from various response formats."""
        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            # Try OpenAI format
            choices = response.get("choices", [])
            if choices and isinstance(choices, list):
                choice = choices[0]
                if isinstance(choice, dict) and "message" in choice:
                    message = choice["message"]
                    if isinstance(message, dict) and "content" in message:
                        return message["content"]

            # Try direct content
            for key in ["content", "text", "response", "output"]:
                if key in response:
                    return str(response[key])

        # Fallback
        return str(response)


class LoopAwareResponseIterator:
    """
    Iterator that works with loop accumulators.
    Provides backward compatibility with BatchVLMResponseIterator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "accumulator": ("ACCUMULATION",),
                "index": ("INT", {"default": 0, "min": 0}),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "BOOLEAN", "STRING")
    RETURN_NAMES = ("response", "total_count", "has_more", "debug_info")
    FUNCTION = "get_response"
    CATEGORY = "VLM/Loop"

    def get_response(self, accumulator, index=0):
        """Get a single response from the accumulator by index."""
        responses = accumulator.get("responses", [])
        total = len(responses)

        if index < total:
            response = responses[index]
            has_more = index < (total - 1)
            debug = f"Response {index + 1} of {total}"
        else:
            response = ""
            has_more = False
            debug = f"Index {index} out of range (total: {total})"

        return (response, total, has_more, debug)


class EnhancedShrugPrompter:
    """
    Enhanced version of ShrugPrompter that accepts template context.
    Maintains backward compatibility while adding memory management.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "user_prompt": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 2048}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.05}),
                "batch_mode": ("BOOLEAN", {"default": False}),
                "processing_mode": (["sequential", "conversation"], {"default": "sequential"}),
            },
            "optional": {
                "context": ("*",),  # Accept any context type
                "system_prompt": ("STRING", {"multiline": True}),
                "mask": ("MASK",),
                "debug_mode": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("LLM_CONTEXT",)
    RETURN_NAMES = ("context",)
    FUNCTION = "generate"
    CATEGORY = "VLM/Core"

    def generate(self, images, user_prompt, max_tokens, temperature, top_p,
                batch_mode, processing_mode, context=None, system_prompt=None,
                mask=None, debug_mode=False):
        """
        Enhanced prompter that handles templates and maintains compatibility.
        Memory efficient with automatic cleanup.
        """
        # Import the original prompter logic
        from .prompter import ShrugPrompter

        # Create instance to use its methods
        original_prompter = ShrugPrompter()

        # If no context, create minimal one
        if context is None:
            context = {
                "provider": "openai",
                "base_url": "http://localhost:8080",
                "api_key": "not-required",
                "llm_model": "gemma3n-e4b-it"
            }

        # Handle template context chaining
        if isinstance(context, dict) and "template" in context:
            # Template was loaded
            if system_prompt is None:
                system_prompt = context.get("template", "You are a helpful assistant.")

        # Add provider info if missing
        if isinstance(context, dict):
            if "provider" not in context:
                context["provider"] = "openai"
            if "base_url" not in context:
                context["base_url"] = "http://localhost:8080"

        # Register images for memory tracking
        memory_tracker.register_tensor(images)

        # Call original prompter logic
        result = original_prompter.execute_prompt(
            system_prompt=system_prompt or "You are a helpful assistant.",
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            provider_config="{}",
            extra_params="{}",
            batch_mode=batch_mode,
            debug_mode=debug_mode,
            return_json=False,
            processing_mode=processing_mode,
            context=context,
            images=images,
            mask=mask
        )

        # Clean up after processing
        memory_tracker.cleanup()

        return result


class RobustImageRangeExtractor:
    """
    Robust version of GetImageRangeFromBatch that handles edge cases.
    Works with ForLoop indices and doesn't fail on boundary conditions.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "num_frames": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                "start_index": ("INT", {"default": 0, "min": 0}),
                "masks": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("IMAGE", "MASK")
    FUNCTION = "extract_range"
    CATEGORY = "VLM/Utility"

    def extract_range(self, images, num_frames=1, start_index=0, masks=None):
        """
        Extract range of images robustly, handling edge cases.
        Returns valid tensors even when indices are out of bounds.
        """
        if images.dim() != 4:
            raise ValueError(f"Expected 4D tensor (B,H,W,C), got {images.dim()}D")

        batch_size = images.shape[0]

        # Clamp start_index to valid range
        start_index = max(0, min(start_index, batch_size - 1))

        # Calculate end index
        end_index = min(start_index + num_frames, batch_size)
        actual_frames = end_index - start_index

        # If we can't extract any frames, return at least one
        if actual_frames <= 0:
            # Return the last frame if we're past the end
            start_index = max(0, batch_size - 1)
            end_index = batch_size
            actual_frames = 1

        # Extract range
        image_range = images[start_index:end_index]

        # Handle masks
        if masks is not None:
            if masks.dim() == 3:  # B,H,W
                mask_range = masks[start_index:end_index]
            else:
                # Create dummy mask
                mask_range = torch.ones((actual_frames, images.shape[1], images.shape[2]),
                                      dtype=torch.float32, device=images.device)
        else:
            # Create dummy mask
            mask_range = torch.ones((actual_frames, images.shape[1], images.shape[2]),
                                  dtype=torch.float32, device=images.device)

        return (image_range, mask_range)


class AccumulationNodeCompat:
    """
    Compatibility node for AccumulationNode/AccumulationGetItemNode patterns.
    Provides clean interface for prompt accumulation in loops.
    """

    _storage = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (["store", "get"], {"default": "store"}),
                "accumulator_id": ("STRING", {"default": "prompts"}),
            },
            "optional": {
                # For store mode
                "item": ("*",),
                "reset": ("BOOLEAN", {"default": False}),
                # For get mode
                "index": ("INT", {"default": 0, "min": 0}),
                "accumulator": ("ACCUMULATION",),
            }
        }

    RETURN_TYPES = ("*", "ACCUMULATION")
    RETURN_NAMES = ("item", "accumulator")
    FUNCTION = "process"
    CATEGORY = "VLM/Loop"

    def process(self, mode, accumulator_id, item=None, reset=False, index=0, accumulator=None):
        """
        Store or retrieve items from accumulation.
        Compatible with AccumulationNode patterns.
        """
        if mode == "store":
            # Store mode
            if reset or accumulator_id not in self._storage:
                self._storage[accumulator_id] = {
                    "items": [],
                    "metadata": {}
                }

            if item is not None:
                self._storage[accumulator_id]["items"].append(item)

            return (item, self._storage[accumulator_id])

        else:
            # Get mode
            if accumulator is None and accumulator_id in self._storage:
                accumulator = self._storage[accumulator_id]

            if accumulator is None:
                return (None, {"items": [], "metadata": {}})

            items = accumulator.get("items", [])
            if 0 <= index < len(items):
                return (items[index], accumulator)
            else:
                return (None, accumulator)
