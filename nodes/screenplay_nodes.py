"""
Screenplay Director Node - Orchestrates the AI Director + Cinematographer workflow

This node implements the "Writers' Room" phase from the two-phase architecture.
It coordinates between the Director (story progression) and Cinematographer (visual details).
"""

import torch
import json
from typing import Dict, Any, Tuple


class ScreenplayDirector:
    """
    Orchestrates the two-step screenplay generation process:
    1. Director LLM generates next action cue based on story arc and progress
    2. Cinematographer LLM converts action cue into detailed VACE prompt

    Integrates with the existing shrug-prompter flow using templates.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),  # Provider context from ProviderSelector
                "story_arc": ("STRING", {
                    "multiline": True,
                    "default": "A character's journey from isolation to connection"
                }),
                "story_so_far": ("STRING", {
                    "multiline": True,
                    "default": "SCENE 1: The story begins..."
                }),
                "last_frame": ("IMAGE",),
                "scene_number": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 100
                }),
                "max_tokens": ("INT", {"default": 256, "min": 1, "max": 32000, "step": 16}),
                "temperature": ("FLOAT", {"default": 1.00, "min": 0.00, "max": 1.99, "step": 0.05}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.00, "max": 1.00, "step": 0.05}),
            },
            "optional": {
                "director_template_override": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "cinematographer_template_override": ("STRING", {
                    "multiline": True,
                    "default": ""
                })
            }
        }

    RETURN_TYPES = ("*", "STRING", "STRING", "STRING", "STRING", "IMAGE", "INT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("context", "director_system", "director_user", "cinematographer_system", "cinematographer_user", "last_frame", "max_tokens", "temperature", "top_p")
    FUNCTION = "prepare_screenplay_prompts"
    CATEGORY = "shrug-prompter/screenplay"

    def prepare_screenplay_prompts(
        self,
        context: Dict[str, Any],
        story_arc: str,
        story_so_far: str,
        last_frame: torch.Tensor,
        scene_number: int,
        max_tokens: int,
        temperature: float,
        top_p: float,
        director_template_override: str = "",
        cinematographer_template_override: str = ""
    ) -> Tuple[Dict[str, Any], str, str, str, str, torch.Tensor, int, float, float]:
        """
        Prepare both director and cinematographer prompts for the two-step process.

        This node sets up the prompts but doesn't make API calls - that's handled
        by ShrugPrompter in the workflow chain.
        """

        # Load default templates if no override provided
        if not director_template_override:
            director_system = self._load_default_director_template()
        else:
            director_system = director_template_override

        if not cinematographer_template_override:
            cinematographer_system = self._load_default_cinematographer_template()
        else:
            cinematographer_system = cinematographer_template_override

        # Build director user prompt
        director_user = self._build_director_user_prompt(
            story_arc, story_so_far, scene_number
        )

        # Build cinematographer user prompt template
        # Note: This will need the director's output, so we create a template
        cinematographer_user = self._build_cinematographer_user_template()

        # Store screenplay metadata in context
        enhanced_context = context.copy()
        enhanced_context["screenplay_metadata"] = {
            "story_arc": story_arc,
            "story_so_far": story_so_far,
            "scene_number": scene_number,
            "workflow_stage": "director_phase"
        }

        return (
            enhanced_context,
            director_system,
            director_user,
            cinematographer_system,
            cinematographer_user,
            last_frame,
            max_tokens,
            temperature,
            top_p
        )

    def _load_default_director_template(self) -> str:
        """Load the default director template."""
        import os
        template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..", "templates", "screenplay_director.md"
        )

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract content after YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    return parts[2].strip()

            return content
        except Exception as e:
            print(f"Warning: Could not load director template: {e}")
            return "You are an AI director. Generate the next logical story action based on the story arc and current progress."

    def _load_default_cinematographer_template(self) -> str:
        """Load the default cinematographer template."""
        import os
        template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..", "templates", "screenplay_cinematographer.md"
        )

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract content after YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    return parts[2].strip()

            return content
        except Exception as e:
            print(f"Warning: Could not load cinematographer template: {e}")
            return "You are an AI cinematographer. Convert action cues into detailed VACE-optimized prompts."

    def _build_director_user_prompt(
        self,
        story_arc: str,
        story_so_far: str,
        scene_number: int
    ) -> str:
        """Build the user prompt for the director."""
        return f"""**Story Arc**: {story_arc}

**Story So Far**: {story_so_far}

**Scene Number**: {scene_number}

Based on the story arc and what has happened so far, what is the next logical action that should occur? Remember to focus on ACTION - what does the character or environment DO next?"""

    def _build_cinematographer_user_template(self) -> str:
        """Build the template for cinematographer user prompt."""
        return """**Action Cue**: The director has decided on the next story beat.

Transform this action cue into a detailed, cinematic, VACE-optimized prompt. Focus on camera work, lighting, movement, and visual details that will create a compelling video segment."""


class ScreenplayAccumulator:
    """
    Accumulates screenplay segments and manages loop state.

    This node handles the concatenation of screenplay segments and maintains
    the story state for the iterative screenplay generation process.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),  # Enhanced context with screenplay metadata
                "new_scene_prompt": ("STRING",),  # Output from cinematographer
                "action_cue": ("STRING",),  # Output from director (for story tracking)
            },
            "optional": {
                "accumulated_screenplay": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "scene_delimiter": ("STRING", {
                    "default": "\n---\n"
                })
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("updated_screenplay", "updated_story_so_far", "next_scene_number")
    FUNCTION = "accumulate_scene"
    CATEGORY = "shrug-prompter/screenplay"

    def accumulate_scene(
        self,
        context: Dict[str, Any],
        new_scene_prompt: str,
        action_cue: str,
        accumulated_screenplay: str = "",
        scene_delimiter: str = "\n---\n"
    ) -> Tuple[str, str, int]:
        """
        Add the new scene to the accumulated screenplay and update story state.
        """

        # Get screenplay metadata from context
        screenplay_meta = context.get("screenplay_metadata", {})
        current_scene = screenplay_meta.get("scene_number", 1)
        story_so_far = screenplay_meta.get("story_so_far", "")

        # Add scene header and prompt to screenplay
        scene_header = f"SCENE {current_scene}:"
        new_scene_block = f"{scene_header} {new_scene_prompt}"

        # Accumulate the screenplay
        if accumulated_screenplay.strip():
            updated_screenplay = accumulated_screenplay + scene_delimiter + new_scene_block
        else:
            updated_screenplay = new_scene_block

        # Update story progress
        story_summary = f"SCENE {current_scene}: {action_cue}"
        if story_so_far.strip():
            updated_story_so_far = story_so_far + "\n" + story_summary
        else:
            updated_story_so_far = story_summary

        next_scene_number = current_scene + 1

        print(f"ScreenplayAccumulator: Added scene {current_scene}")
        print(f"Total screenplay length: {len(updated_screenplay)} characters")

        return (updated_screenplay, updated_story_so_far, next_scene_number)


class ScreenplayFormatter:
    """
    Formats the completed screenplay for WanVideoWrapper consumption.

    This node handles the final formatting step, converting the accumulated
    screenplay into the pipe-separated format required by WanVideoWrapper.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),  # Provider context for potential LLM formatting
                "accumulated_screenplay": ("STRING", {"multiline": True}),
            },
            "optional": {
                "scene_delimiter": ("STRING", {"default": "\n---\n"}),
                "output_delimiter": ("STRING", {"default": " | "}),
                "use_llm_formatting": ("BOOLEAN", {"default": False}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 32000}),
                "temperature": ("FLOAT", {"default": 0.30, "min": 0.00, "max": 1.00}),
            }
        }

    RETURN_TYPES = ("STRING", "*", "STRING", "STRING", "IMAGE", "INT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("formatted_screenplay", "context", "system_prompt", "user_prompt", "images", "max_tokens", "temperature", "top_p")
    FUNCTION = "format_screenplay"
    CATEGORY = "shrug-prompter/screenplay"

    def format_screenplay(
        self,
        context: Dict[str, Any],
        accumulated_screenplay: str,
        scene_delimiter: str = "\n---\n",
        output_delimiter: str = " | ",
        use_llm_formatting: bool = False,
        max_tokens: int = 512,
        temperature: float = 0.3
    ) -> Tuple[str, Dict[str, Any], str, str, torch.Tensor, int, float, float]:
        """
        Format the screenplay for WanVideoWrapper or prepare for LLM formatting.
        """

        if not use_llm_formatting:
            # Simple string processing
            formatted = self._simple_format(accumulated_screenplay, scene_delimiter, output_delimiter)

            # Return with empty values for LLM parameters
            empty_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            return (
                formatted,
                context,
                "",  # No system prompt needed
                "",  # No user prompt needed
                empty_image,
                max_tokens,
                temperature,
                0.9  # top_p
            )
        else:
            # Prepare for LLM formatting
            system_prompt = self._load_formatter_template()
            user_prompt = f"Format this screenplay for WanVideoWrapper:\n\n{accumulated_screenplay}"

            enhanced_context = context.copy()
            enhanced_context["screenplay_metadata"] = {
                "workflow_stage": "formatting_phase"
            }

            empty_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            return (
                "",  # Will be filled by subsequent LLM call
                enhanced_context,
                system_prompt,
                user_prompt,
                empty_image,
                max_tokens,
                temperature,
                0.9  # top_p
            )

    def _simple_format(
        self,
        screenplay: str,
        input_delimiter: str,
        output_delimiter: str
    ) -> str:
        """Simple string-based formatting without LLM."""

        # Split by scene delimiter
        scenes = screenplay.split(input_delimiter)

        formatted_scenes = []
        for scene in scenes:
            scene = scene.strip()
            if not scene:
                continue

            # Remove scene headers (SCENE X:)
            if scene.startswith("SCENE ") and ":" in scene:
                colon_index = scene.find(":")
                scene = scene[colon_index + 1:].strip()

            # Clean up extra whitespace
            scene = " ".join(scene.split())

            if scene:
                formatted_scenes.append(scene)

        # Join with output delimiter
        result = output_delimiter.join(formatted_scenes)

        print(f"ScreenplayFormatter: Formatted {len(formatted_scenes)} scenes")
        print(f"Output length: {len(result)} characters")

        return result

    def _load_formatter_template(self) -> str:
        """Load the formatter template for LLM-based formatting."""
        import os
        template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..", "templates", "screenplay_formatter.md"
        )

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract content after YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    return parts[2].strip()

            return content
        except Exception as e:
            print(f"Warning: Could not load formatter template: {e}")
            return "Format the screenplay by removing scene numbers and joining with pipe separators."
