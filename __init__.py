# __init__.py

from .univerisal_vlm_prompter import UniversalVLMPrompter
from .prompt_template_loader import PromptTemplateLoader

NODE_CLASS_MAPPINGS = {
    "UniversalVLMPrompter_Shrug": UniversalVLMPrompter,
    "PromptTemplateLoader_Shrug": PromptTemplateLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UniversalVLMPrompter_Shrug": "Universal VLM Prompter (Shrug)",
    "PromptTemplateLoader_Shrug": "Prompt Template Loader (Shrug)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
