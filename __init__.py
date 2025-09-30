# __init__.py

# ============================================================================
# NODE REGISTRATION
# ============================================================================

# Initialize mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import all node classes
try:
    from .nodes.provider_selector import ShrugProviderSelector
    from .nodes.prompter import ShrugPrompter
    from .nodes.core_vlm_nodes import VLMPrompter, VLMImageProcessor, VLMResultCollector, VLMResultIterator
    from .nodes.video_workflow_nodes import VideoFramePairExtractor, VideoSegmentAssembler, SmartImageRangeExtractor, AutoMemoryManager
    from .nodes.prompt_template_loader import PromptTemplateLoader
    from .nodes.loop_accumulator import LoopSafeAccumulator
    from .nodes.prompt_batch_loader import ShrugPromptBatchFromFile
    from .nodes.vlm_passthrough import VLMImagePassthrough, VLMImageResizer
    from .nodes.type_helpers import AnyTypePassthrough, ImageToAny
    from .nodes.text_list_converter import TextListToString, TextListIndexer
    from .nodes.advanced_sampler import AdvancedVLMSampler
    from .nodes.loop_compatible_nodes import LoopAwareVLMAccumulator, LoopAwareResponseIterator, RobustImageRangeExtractor, AccumulationNodeCompat
    from .nodes.text_cleanup import TextCleanupNode, TextListCleanupNode
    from .nodes.memory_cleanup import GlobalMemoryCleanup
    from .nodes.remote_text_encoder import RemoteTextEncoder
    from .nodes.seed_prompt_generator import SeedPromptGenerator
    from .nodes.two_round_vlm import TwoRoundVLMPrompter, VLMStyleRewriter, DualProviderConfig
    from .nodes.audio_utils import LoadAudio
    from .nodes.asr_prompter import ShrugASRNode

    # Populate mappings within the try block
    NODE_CLASS_MAPPINGS.update({
        "VLMProviderConfig": ShrugProviderSelector, "ShrugPrompter": ShrugPrompter, "VLMPrompterFast": VLMPrompter,
        "VLMImageProcessor": VLMImageProcessor, "VLMResultCollector": VLMResultCollector, "VLMResultIterator": VLMResultIterator,
        "VideoFramePairExtractor": VideoFramePairExtractor, "VideoSegmentAssembler": VideoSegmentAssembler,
        "SmartImageRangeExtractor": SmartImageRangeExtractor, "AutoMemoryManager": AutoMemoryManager, "GlobalMemoryCleanup": GlobalMemoryCleanup,
        "PromptTemplateLoader": PromptTemplateLoader, "LoopSafeAccumulator": LoopSafeAccumulator, "ShrugPromptBatchFromFile": ShrugPromptBatchFromFile,
        "VLMImagePassthrough": VLMImagePassthrough, "VLMImageResizer": VLMImageResizer, "ImageToAny": ImageToAny,
        "AnyTypePassthrough": AnyTypePassthrough, "TextListToString": TextListToString, "TextListIndexer": TextListIndexer,
        "TextCleanup": TextCleanupNode, "TextListCleanup": TextListCleanupNode, "LoopAwareVLMAccumulator": LoopAwareVLMAccumulator,
        "LoopAwareResponseIterator": LoopAwareResponseIterator, "RobustImageRangeExtractor": RobustImageRangeExtractor,
        "AccumulationNodeCompat": AccumulationNodeCompat, "AdvancedVLMSampler": AdvancedVLMSampler, "RemoteTextEncoder": RemoteTextEncoder,
        "SeedPromptGenerator": SeedPromptGenerator, "TwoRoundVLMPrompter": TwoRoundVLMPrompter, "VLMStyleRewriter": VLMStyleRewriter,
        "DualProviderConfig": DualProviderConfig, "LoadAudio": LoadAudio, "ShrugASRNode": ShrugASRNode,
    })

    NODE_DISPLAY_NAME_MAPPINGS.update({
        "VLMProviderConfig": "VLM Provider Config", "ShrugPrompter": "Shrug Prompter", "VLMPrompterFast": "VLM Prompter Fast",
        "VLMImageProcessor": "VLM Image Processor", "VLMResultCollector": "VLM Result Collector", "VLMResultIterator": "VLM Result Iterator",
        "VideoFramePairExtractor": "Video Frame Pair Extractor", "VideoSegmentAssembler": "Video Segment Assembler",
        "SmartImageRangeExtractor": "Smart Image Range Extractor", "AutoMemoryManager": "Auto Memory Manager",
        "GlobalMemoryCleanup": "Global Memory Cleanup", "PromptTemplateLoader": "Prompt Template Loader",
        "LoopSafeAccumulator": "Loop Safe Accumulator", "ShrugPromptBatchFromFile": "Load Prompt Batch From File",
        "VLMImagePassthrough": "VLM Image Passthrough (Zero Copy)", "VLMImageResizer": "VLM Image Resizer (Minimal)",
        "ImageToAny": "Image to Any Type", "AnyTypePassthrough": "Any Type Passthrough", "TextListToString": "Text List to String",
        "TextListIndexer": "Text List Indexer", "TextCleanup": "Text Cleanup", "TextListCleanup": "Text List Cleanup",
        "LoopAwareVLMAccumulator": "Loop Aware VLM Accumulator", "LoopAwareResponseIterator": "Loop Aware Response Iterator",
        "RobustImageRangeExtractor": "Robust Image Range Extractor", "AccumulationNodeCompat": "Accumulation Node Compat",
        "AdvancedVLMSampler": "Advanced VLM Sampler", "RemoteTextEncoder": "Remote Text Encoder", "SeedPromptGenerator": "Seed Prompt Generator",
        "TwoRoundVLMPrompter": "Two-Round VLM Prompter", "VLMStyleRewriter": "VLM Style Rewriter", "DualProviderConfig": "Dual Provider Config",
        "LoadAudio": "Load Audio File", "ShrugASRNode": "Shrug Speech-to-Text (ASR)",
    })

except ImportError as e:
    print(f"[shrug-prompter] CRITICAL: Could not import one or more nodes. This is a fatal error. Please check dependencies. Error: {e}")


print(f"[shrug-prompter] Total nodes loaded: {len(NODE_CLASS_MAPPINGS)}")

# ============================================================================
# SERVER EXTENSIONS
# ============================================================================
# check for the existence of the server instance to determine if we are running in ComfyUI
try:
    import comfy.server
    from aiohttp import web
    from .utils import get_models

    if hasattr(comfy.server, "PromptServer") and comfy.server.PromptServer.instance is not None:

        @web.middleware
        async def browser_middleware(request, handler):
            response = await handler(request)
            if 'Cache-Control' not in response.headers:
                response.headers['Cache-Control'] = 'no-cache'
            return response

        # Add the routes directly to the server instance
        PromptServer = comfy.server.PromptServer.instance
        PromptServer.app.add_routes([
            web.get('/shrug/get_models', get_models_handler)
        ])

        # Add the middleware to disable caching for our JS file
        PromptServer.app.middlewares.append(browser_middleware)

        async def get_models_handler(request):
            """Handle model fetching requests from the frontend"""
            provider = request.query.get("provider", "openai")
            base_url = request.query.get("base_url", "http://localhost:8080")
            api_key = request.query.get("api_key", "")
            try:
                models = get_models(provider, api_key, base_url)
                return web.json_response({"success": True, "models": models, "provider": provider})
            except Exception as e:
                print(f"[Shrug-Prompter] Error fetching models: {e}")
                return web.json_response(
                    {"success": False, "error": f"Failed to fetch models: {str(e)}", "provider": provider},
                    status=500,
                )

        print("[Shrug-Prompter] Server routes for model fetching registered successfully.")

except (ImportError, AttributeError, NameError):
    pass


# ============================================================================
# EXPORTS FOR COMFYUI
# ============================================================================
WEB_DIRECTORY = "web" # Changed from "./web" to "web" for better compatibility
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
