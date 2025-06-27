from .llm_prompter import *
from .director_llm import *

# --- ComfyUI Boilerplate ---
NODE_CLASS_MAPPINGS = {
    "LLMPromptGenerator_VACE": LLMPromptGenerator,
    "DirectorLLMNode": DirectorLLMNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LLMPromptGenerator_VACE": "VACE LLM Prompt Generator",
    "DirectorLLMNode": "Director LLM Node"
}
