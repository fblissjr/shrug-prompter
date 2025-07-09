"""
Automated Director Task Decomposer Node for WAN VACE Workflows

This node integrates with the shrug-prompter system to automatically decompose
high-level goals into sequential prompts and organize images accordingly.

Uses the proper shrug-prompter flow:
ProviderSelector → AutomatedDirector → ShrugPrompter → ShrugResponseParser
"""

import torch
import numpy as np
from typing import List, Tuple, Any, Dict
import json
import math


class AutomatedDirector:
    """
    Automated director node that prepares director prompts and batches images.
    Integrates with the shrug-prompter system instead of bypassing it.

    This node focuses on director-specific logic:
    - Building director system and user prompts
    - Calculating image batching parameters
    - Converting images to proper format for ShrugPrompter

    API communication is handled by ShrugPrompter, not this node.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),  # Provider context from ProviderSelector
                "overarching_goal": ("STRING", {
                    "multiline": True,
                    "default": "Create a smooth video sequence"
                }),
                "images": ("IMAGE",),
                "images_per_prompt": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 10,
                    "step": 1
                }),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 32000}),
                "temperature": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 2.00}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.00, "max": 1.00}),
            },
            "optional": {
                "system_prompt_override": ("STRING", {
                    "multiline": True,
                    "default": ""
                })
            }
        }

    RETURN_TYPES = ("*", "STRING", "STRING", "IMAGE", "INT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("context", "system_prompt", "user_prompt", "images", "max_tokens", "temperature", "top_p")
    FUNCTION = "prepare_director_prompt"
    CATEGORY = "shrug-prompter/automation"

    def prepare_director_prompt(
        self,
        context: Dict[str, Any],
        overarching_goal: str,
        images: torch.Tensor,
        images_per_prompt: int,
        max_tokens: int,
        temperature: float,
        top_p: float,
        system_prompt_override: str = ""
    ) -> Tuple[Dict[str, Any], str, str, torch.Tensor, int, float, float]:
        """
        Prepare director prompts and pass through the context for ShrugPrompter.

        This node focuses on director-specific logic only. The actual API call
        will be handled by ShrugPrompter using the context and prompts we provide.
        """

        # Calculate number of segments based on images and desired batch size
        batch_size = images.shape[0]
        num_segments = max(1, math.ceil(batch_size / images_per_prompt))

        # Build system prompt for director task decomposition
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = self._build_director_system_prompt()

        # Build user prompt with goal and context
        user_prompt = self._build_user_prompt(overarching_goal, batch_size, num_segments, images_per_prompt)

        # Store director metadata in context for downstream processing
        enhanced_context = context.copy()
        enhanced_context["director_metadata"] = {
            "overarching_goal": overarching_goal,
            "total_images": batch_size,
            "num_segments": num_segments,
            "images_per_prompt": images_per_prompt
        }

        # Return everything needed for ShrugPrompter
        return (
            enhanced_context,
            system_prompt,
            user_prompt,
            images,  # Pass images through for ShrugPrompter
            max_tokens,
            temperature,
            top_p
        )

    def _build_director_system_prompt(self) -> str:
        """Build the system prompt for the director task decomposer."""
        return """You are a master cinematographer and video director. Your task is to analyze keyframe images and break down high-level video goals into sequential, detailed prompts for video generation.

Focus on:
- Cinematic camera movements and angles
- Lighting and atmospheric transitions
- Character continuity and natural motion
- Environmental and setting changes
- Micro-movements that create depth and life
- Smooth narrative and visual progression

Return ONLY a valid JSON array of strings. Each string should be a detailed prompt for one video segment that will create smooth transitions between the provided keyframes."""

    def _build_user_prompt(
        self,
        goal: str,
        total_images: int,
        num_segments: int,
        images_per_segment: int
    ) -> str:
        """Build the user prompt for the director task decomposer."""
        return f"""Goal: {goal}

Available: {total_images} keyframe images
Target: {num_segments} video segments
Images per segment: {images_per_segment}

Analyze the provided keyframe images and break down this goal into {num_segments} sequential video prompts. Each prompt should describe a distinct cinematic phase that will create smooth video transitions between the keyframes.

Focus on camera work, lighting, character movement, and atmospheric details that will result in professional, cinematic video generation.

Return as a JSON array of {num_segments} detailed prompts."""


class AutomatedDirectorImageBatcher:
    """
    Companion node to process the JSON response and batch images accordingly.

    This separates the image batching logic from the prompt generation logic,
    following the separation of concerns principle in the shrug-prompter system.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),  # Enhanced context with director metadata
                "parsed_prompts": ("STRING",),  # Output from ShrugResponseParser
                "images": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE")
    RETURN_NAMES = ("prompts_json", "batched_images")
    FUNCTION = "batch_images_with_prompts"
    CATEGORY = "shrug-prompter/automation"

    def batch_images_with_prompts(
        self,
        context: Dict[str, Any],
        parsed_prompts: str,
        images: torch.Tensor
    ) -> Tuple[str, torch.Tensor]:
        """
        Batch images according to the director's decomposed prompts.

        Takes the parsed JSON response and batches images appropriately.
        """

        # Get director metadata from context
        director_meta = context.get("director_metadata", {})
        images_per_prompt = director_meta.get("images_per_prompt", 3)
        num_segments = director_meta.get("num_segments", 1)

        try:
            # Parse the prompts (should already be parsed by ShrugResponseParser)
            if parsed_prompts.startswith('[') and parsed_prompts.endswith(']'):
                prompts = json.loads(parsed_prompts)
            else:
                # If it's not JSON, treat as single prompt
                prompts = [parsed_prompts]

            if not isinstance(prompts, list):
                prompts = [str(prompts)]

        except (json.JSONDecodeError, ValueError) as e:
            print(f"AutomatedDirectorImageBatcher: JSON parsing failed: {e}")
            print(f"Raw response: {parsed_prompts}")
            # Fallback: use the raw response as a single prompt
            prompts = [parsed_prompts]

        # Ensure we have the right number of prompts
        while len(prompts) < num_segments:
            prompts.append(prompts[-1] if prompts else "Continue the sequence")
        prompts = prompts[:num_segments]

        # Batch images according to the prompts
        image_batches = self._batch_images(images, images_per_prompt)

        # Combine all batches into a single tensor for processing
        combined_images = torch.cat(image_batches, dim=0) if image_batches else images

        # Return as JSON string and combined image batch
        prompts_json = json.dumps(prompts)

        return (prompts_json, combined_images)

    def _batch_images(
        self,
        images: torch.Tensor,
        batch_size: int
    ) -> List[torch.Tensor]:
        """
        Batch images for processing.

        Simple batching without overlap for this implementation.
        """
        batches = []
        total_images = images.shape[0]

        start_idx = 0
        while start_idx < total_images:
            end_idx = min(start_idx + batch_size, total_images)
            batch = images[start_idx:end_idx]

            # Pad if necessary (ensure consistent batch size for processing)
            if batch.shape[0] < batch_size and start_idx > 0:
                padding_needed = batch_size - batch.shape[0]
                last_frame = batch[-1:].repeat(padding_needed, 1, 1, 1)
                batch = torch.cat([batch, last_frame], dim=0)

            batches.append(batch)
            start_idx = end_idx

            if start_idx >= total_images:
                break

        return batches
