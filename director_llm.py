# In ComfyUI/custom_nodes/director_llm.py

import torch
import numpy as np
from PIL import Image
import os

try:
    from google import genai
    print("Google GenAI library loaded successfully for Director node.")
except ImportError:
    print("----------------------------------------------------------------")
    print("ERROR: Google GenAI library not found for Director node.")
    print("Please ensure it is installed: pip install google-generativeai")
    print("----------------------------------------------------------------")
    pass

# The system prompt that defines the "Director's" job.
DIRECTOR_SYSTEM_PROMPT = """You are a creative and logical screenwriter. Your task is to advance a story, one scene at a time. You will be given a high-level 'Story Arc', the 'Story So Far', and the last visual frame from the previous scene.

Your single objective is to output the **very next logical action** that moves the story forward towards the goal of the Story Arc.

RULES:
1.  Output ONLY a single, simple sentence.
2.  Focus on ACTION. What does the character or environment DO next?
3.  Do NOT be descriptive or cinematic. That is for a different AI.
4.  Do not repeat actions from the 'Story So Far'.
5.  Keep your output concise and clear.

**Example:**
- Story Arc: "A detective investigates a haunted house."
- Story So Far: "1. The detective arrives at the gates."
- Last Frame: (Image of the detective at the gates)
- Your Output: The detective cautiously pushes the gate open.
"""

class DirectorLLMNode:
    """
    An LLM node that acts as a "Director," determining the next
    plot point in a sequence based on a high-level arc and the story so far.
    """
    def __init__(self):
        self.client_initialized = False
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            # The genai library is configured globally by the other node,
            # so we just need to confirm it was successful.
            genai.configure(api_key=api_key)
            self.client_initialized = True
        else:
            print("WARNING: GEMINI_API_KEY not set. DirectorLLMNode will not work.")

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "last_frame": ("IMAGE",),
                "story_arc": ("STRING", {"multiline": True, "default": "A lone astronaut explores a mysterious, glowing alien forest, with the mood slowly turning from wonder to terror."}),
                "story_so_far": ("STRING", {"multiline": True, "default": "INITIAL SCENE:"}),
                "sequence_number": ("INT", {"default": 1, "min": 1, "max": 100}),
                "model": (["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("next_action_cue", "new_story_so_far",)
    FUNCTION = "decide_next_action"
    CATEGORY = "logic/llm"

    def tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        image_np = tensor.squeeze(0).cpu().numpy()
        image_np = (image_np * 255).astype(np.uint8)
        return Image.fromarray(image_np)

    def decide_next_action(self, last_frame, story_arc, story_so_far, sequence_number, model):
        if not self.client_initialized:
            return ("ERROR: Gemini Client not initialized.", story_so_far)

        try:
            generative_model = genai.GenerativeModel(model)
            pil_image = self.tensor_to_pil(last_frame)

            full_prompt_to_llm = f"""{DIRECTOR_SYSTEM_PROMPT}

---
**Story Arc:** {story_arc}
**Story So Far:**
{story_so_far}

---
Based on all the above, what is the single action for scene #{sequence_number}?
"""
            response = generative_model.generate_content([full_prompt_to_llm, pil_image])

            next_action = response.text.strip()

            # Update the story state for the next loop iteration
            new_story = f"{story_so_far}\n{sequence_number}. {next_action}"

            print(f"Director's Decided Action Cue (Seq {sequence_number}): {next_action}")

            return (next_action, new_story,)

        except Exception as e:
            error_message = f"ERROR in DirectorLLMNode: {e}"
            print(error_message)
            return (error_message, story_so_far)
