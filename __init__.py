# shrug-prompter/__init__.py

from .nodes import ShrugPrompter
from .nodes import ShrugProviderSelector
from .nodes import ShrugResponseParser, JSONStringToList
from .nodes import PromptTemplateLoader
from .nodes import ShrugMaskUtilities
from .nodes import AutomatedDirector, AutomatedDirectorImageBatcher
from .nodes import ScreenplayDirector, ScreenplayAccumulator, ScreenplayFormatter

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

WEB_DIRECTORY = "./js"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print("✓ Shrug Prompter (v3 - Final) nodes loaded.")
# --- Web Server Endpoints ---
# Enhanced endpoint with caching and better error handling to complement
# the improved frontend JavaScript.

try:
    from aiohttp import web
    from server import PromptServer
    import time
    import asyncio

    try:
        from .utils import get_models
    except ImportError:
        from utils import get_models

    # Simple server-side cache to reduce API calls
    _model_cache = {}
    _cache_timeout = 5 * 60  # 5 minutes to match frontend cache

    def _create_cache_key(provider, base_url):
        """Create cache key for model requests."""
        return f"{provider}:{base_url}"

    def _is_cache_valid(cache_entry):
        """Check if cache entry is still valid."""
        return cache_entry and (time.time() - cache_entry['timestamp']) < _cache_timeout

    @PromptServer.instance.routes.get("/shrug/get_models")
    async def get_shrug_models_endpoint(request):
        """
        Enhanced model fetching endpoint with caching and robust error handling.
        Query parameters: provider, api_key, base_url
        """
        provider = request.query.get("provider")
        api_key = request.query.get("api_key", "")
        base_url = request.query.get("base_url")

        # Validate required parameters
        if not provider or not base_url:
            return web.json_response(
                {"error": "provider and base_url parameters are required"},
                status=400
            )

        # Check cache first
        cache_key = _create_cache_key(provider, base_url)
        cached_entry = _model_cache.get(cache_key)

        if _is_cache_valid(cached_entry):
            print(f"Shrug: Returning cached models for {provider} at {base_url}")
            return web.json_response(cached_entry['models'])

        try:
            print(f"Shrug: Fetching fresh models for {provider} at {base_url}")

            # Run get_models in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(
                None,
                lambda: get_models(provider, api_key, base_url)
            )

            # Validate response
            if not models or not isinstance(models, list):
                raise ValueError("Invalid model response format")

            # Filter out error messages that might be in the model list
            valid_models = [
                model for model in models
                if isinstance(model, str) and
                not any(err in model.lower() for err in ['error', 'timeout', 'failed'])
            ]

            if not valid_models:
                raise ValueError("No valid models found")

            # Cache the successful result
            _model_cache[cache_key] = {
                'models': valid_models,
                'timestamp': time.time()
            }

            # Cleanup old cache entries to prevent memory growth
            if len(_model_cache) > 20:  # Keep reasonable cache size
                oldest_key = min(_model_cache.keys(),
                               key=lambda k: _model_cache[k]['timestamp'])
                del _model_cache[oldest_key]

            print(f"Shrug: Successfully fetched {len(valid_models)} models")
            return web.json_response(valid_models)

        except asyncio.TimeoutError:
            error_msg = f"Timeout fetching models from {base_url}"
            print(f"ERROR: {error_msg}")
            return web.json_response({"error": error_msg}, status=408)

        except ConnectionError as e:
            error_msg = f"Connection failed to {base_url}: {str(e)}"
            print(f"ERROR: {error_msg}")
            return web.json_response({"error": error_msg}, status=503)

        except ValueError as e:
            error_msg = f"Invalid response from {base_url}: {str(e)}"
            print(f"ERROR: {error_msg}")
            return web.json_response({"error": error_msg}, status=422)

        except Exception as e:
            error_msg = f"Unexpected error fetching models: {str(e)}"
            print(f"ERROR in /shrug/get_models endpoint: {error_msg}")
            return web.json_response({"error": error_msg}, status=500)

    print("✓ Shrug Prompter unified nodes loaded with web endpoints")

except ImportError as e:
    print(f"Warning: Could not import ComfyUI server components: {e}")
    print("API endpoint for Shrug Prompter not available.")
    print("--- Shrug Prompter unified nodes loaded (standalone mode) ---")
