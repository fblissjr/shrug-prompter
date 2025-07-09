"""
Shrug Prompter Nodes for ComfyUI

This package provides prompt enhancement and automation nodes for ComfyUI,
with special focus on video generation workflows and task decomposition.
"""

from .prompter import ShrugPrompter
from .provider_selector import ShrugProviderSelector
from .response_parser import ShrugResponseParser, JSONStringToList
from .prompt_template_loader import PromptTemplateLoader
from .mask_utils import ShrugMaskUtilities
from .automated_director import AutomatedDirector, AutomatedDirectorImageBatcher
from .screenplay_nodes import ScreenplayDirector, ScreenplayAccumulator, ScreenplayFormatter

# Node class mappings for ComfyUI registration
NODE_CLASS_MAPPINGS = {
    "ShrugPrompter": ShrugPrompter,
    "AutomatedDirector": AutomatedDirector,
    "AutomatedDirectorImageBatcher": AutomatedDirectorImageBatcher,
    "ScreenplayDirector": ScreenplayDirector,
    "ScreenplayAccumulator": ScreenplayAccumulator,
    "ScreenplayFormatter": ScreenplayFormatter,
    "ShrugProviderSelector": ShrugProviderSelector,
    "ShrugResponseParser": ShrugResponseParser,
    "JSONStringToList": JSONStringToList,
    "PromptTemplateLoader_Shrug": PromptTemplateLoader,
    "ShrugMaskUtilities": ShrugMaskUtilities
}

# Display names for the ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "ShrugPrompter": "VLM Prompter (Shrug)",
    "AutomatedDirector": "Automated Director (WAN VACE)",
    "AutomatedDirectorImageBatcher": "Director Image Batcher (WAN VACE)",
    "ScreenplayDirector": "Screenplay Director (AI Writers' Room)",
    "ScreenplayAccumulator": "Screenplay Accumulator (Writers' Room)",
    "ScreenplayFormatter": "Screenplay Formatter (Film Set)",
    "ShrugProviderSelector": "Provider Selector (Shrug)",
    "ShrugResponseParser": "Response Parser (Shrug)",
    "JSONStringToList": "JSON String to List",
    "PromptTemplateLoader_Shrug": "Prompt Template Loader (Shrug)",
    "ShrugMaskUtilities": "Mask Utilities (Shrug)"
}

# Export for external imports
__all__ = [
    "ShrugPrompter",
    "AutomatedDirector",
    "AutomatedDirectorImageBatcher",
    "ScreenplayDirector",
    "ScreenplayAccumulator",
    "ScreenplayFormatter",
    "ShrugProviderSelector",
    "ShrugResponseParser",
    "JSONStringToList",
    "PromptTemplateLoader",
    "ShrugMaskUtilities"
]
