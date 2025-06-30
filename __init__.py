__init__.py

from .universal_vlm_prompter import UniversalVLMPrompter
from .prompt_template_loader import PromptTemplateLoader

NODE_CLASS_MAPPINGS = {
    "UniversalVLMPrompter_Shrug": UniversalVLMPrompter,
    "PromptTemplateLoader_Shrug": PromptTemplateLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UniversalVLMPrompter_Shrug": "Universal VLM Prompter",
    "PromptTemplateLoader_Shrug": "Prompt Template Loader",
}
