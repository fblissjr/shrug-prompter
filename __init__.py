"""
Shrug-Prompter
- Clean, memory-efficient VLM nodes for ComfyUI, with state management, looping, keyframe extraction, batching, and built-in templates for Wan2.1, VACE, and beyond
- Initially built and tested with my local vision LLM server, https://github.com/fblissjr/heylookitsanllm - but will work with any OpenAI API server spec
- Built for Wan2.1, VACE, and FLUX Kontext, but obviously can be extended beyond that
- Handles State Management Looping, Batching, Keyframe Extraction, and many more edge cases that drove me crazy when building this project
- Built with love for Bandoco (and the broader community), where I've learned a ton over the years, and where all the amazing innovation in this space is happening right now
"""

# Core VLM Operations (4 nodes)
from .nodes.provider_selector import ShrugProviderSelector as VLMProviderConfig
from .nodes.prompter import ShrugPrompter
from .nodes.core_vlm_nodes import (
    VLMPrompter,  # New memory-efficient version
    VLMImageProcessor,
    VLMResultCollector,
    VLMResultIterator,
)

# Video Workflow (5 nodes)
from .nodes.video_workflow_nodes import (
    VideoFramePairExtractor,
    VideoSegmentAssembler,
    SmartImageRangeExtractor,
    AutoMemoryManager,
)

# Utilities (2 nodes)
from .nodes.prompt_template_loader import PromptTemplateLoader
from .nodes.loop_accumulator import LoopSafeAccumulator  # Keep for ForLoop compatibility

# Loop Compatibility (5 nodes)
from .nodes.loop_compatible_nodes import (
    LoopAwareVLMAccumulator,
    LoopAwareResponseIterator,
    EnhancedShrugPrompter,
    RobustImageRangeExtractor,
    AccumulationNodeCompat,
)

# ===== notes to self after major refactor =====
# old nodes to new nodes mappings:
#
# Image Processing:
# - BatchImageProcessor -> VLMImageProcessor
# - SmartImageProcessor -> VLMImageProcessor
# - VLMImageOptimizer -> VLMImageProcessor
# - WanVideoCompatibilityProcessor -> VLMImageProcessor (mode="prepare_for_video")
#
# Response Handling:
# - ShrugResponseParser -> Built into VLMPrompter
# - BatchResponseParser -> Built into VLMPrompter
# - EnhancedResponseParser -> Built into VLMPrompter
#
# Accumulation:
# - BatchVLMAccumulator -> VLMResultCollector
# - DynamicPromptAccumulator -> VLMResultCollector
# - BatchVLMResponseIterator -> VLMResultIterator
#
# Video:
# - ImagePairIterator -> VideoFramePairExtractor
# - ImageBatchReassembler -> VideoSegmentAssembler
# - ImageRangeExtractor -> SmartImageRangeExtractor
#
# Memory:
# - MemoryManagementNode -> AutoMemoryManager
# - MemoryManager -> AutoMemoryManager

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    # Core VLM nodes
    "VLMProviderConfig": VLMProviderConfig,
    "ShrugPrompter": EnhancedShrugPrompter,  # main prompter with all features
    "VLMPrompterFast": VLMPrompter,  # more lightweight alternative
    "VLMImageProcessor": VLMImageProcessor,
    "VLMResultCollector": VLMResultCollector,
    "VLMResultIterator": VLMResultIterator,

    # Video Workflow Nodes
    "VideoFramePairExtractor": VideoFramePairExtractor,
    "VideoSegmentAssembler": VideoSegmentAssembler,
    "SmartImageRangeExtractor": SmartImageRangeExtractor,
    "AutoMemoryManager": AutoMemoryManager,

    # Utility Nodes
    "PromptTemplateLoader": PromptTemplateLoader,
    "LoopSafeAccumulator": LoopSafeAccumulator,

    # Loop Compatibility Nodes to deal with State Management
    "LoopAwareVLMAccumulator": LoopAwareVLMAccumulator,
    "LoopAwareResponseIterator": LoopAwareResponseIterator,
    "RobustImageRangeExtractor": RobustImageRangeExtractor,
    "AccumulationNodeCompat": AccumulationNodeCompat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Core VLM nodes
    "VLMProviderConfig": "VLM Provider Config",
    "ShrugPrompter": "Shrug Prompter",
    "VLMPrompterFast": "VLM Prompter Fast",
    "VLMImageProcessor": "VLM Image Processor",
    "VLMResultCollector": "VLM Result Collector",
    "VLMResultIterator": "VLM Result Iterator",

    # Video Workflow Nodes
    "VideoFramePairExtractor": "Video Frame Pair Extractor",
    "VideoSegmentAssembler": "Video Segment Assembler",
    "SmartImageRangeExtractor": "Smart Image Range Extractor",
    "AutoMemoryManager": "Auto Memory Manager",

    # Utility Nodes
    "PromptTemplateLoader": "Prompt Template Loader",
    "LoopSafeAccumulator": "Loop Safe Accumulator",

    # Loop Compatibility Nodes to deal with State Management
    "LoopAwareVLMAccumulator": "Loop Aware VLM Accumulator",
    "LoopAwareResponseIterator": "Loop Aware Response Iterator",
    "RobustImageRangeExtractor": "Robust Image Range Extractor",
    "AccumulationNodeCompat": "Accumulation Node Compat",
}

print(f"[Shrug-Prompter] Loaded {len(NODE_CLASS_MAPPINGS)} nodes")
print("[Shrug-Prompter] Memory management: Automatic")
print("[Shrug-Prompter] From 36 nodes → 17 essential nodes")

# Add ComfyUI server routes for model fetching
from aiohttp import web
import aiohttp
import json

routes = web.RouteTableDef()

@routes.get("/shrug/get_models")
async def get_models_handler(request):
    """Handle model fetching requests from the frontend"""
    provider = request.query.get("provider", "openai")
    base_url = request.query.get("base_url", "http://localhost:8080")
    api_key = request.query.get("api_key", "")

    try:
        # Import the utility function
        from .utils import get_models

        # Get models from the provider
        models = get_models(provider, api_key, base_url)

        # Return as JSON
        return web.json_response(models)

    except Exception as e:
        print(f"[Shrug-Prompter] Error fetching models: {e}")
        return web.json_response(
            {"error": f"Failed to fetch models: {str(e)}"},
            status=500
        )

# Export routes and web directory for ComfyUI
WEB_DIRECTORY = "./js"
NODE_CLASS_MAPPINGS  # Already defined above
NODE_DISPLAY_NAME_MAPPINGS  # Already defined above
