# __init__.py

# --- Node Class Mappings ---
# This section imports node classes and maps them to their internal names
# and display names for ComfyUI. A unique suffix is recommended to avoid
# conflicts with other custom node packages.

try:
    from .nodes.provider_selector import ShrugProviderSelector
    from .nodes.prompter import ShrugPrompter
    from .nodes.response_parser import ShrugResponseParser
    from .nodes.prompt_template_loader import PromptTemplateLoader
except ImportError:
    # Fallback for testing
    from nodes.provider_selector import ShrugProviderSelector
    from nodes.prompter import ShrugPrompter
    from nodes.response_parser import ShrugResponseParser
    from nodes.prompt_template_loader import PromptTemplateLoader

NODE_CLASS_MAPPINGS = {
    "ShrugProviderSelector": ShrugProviderSelector,
    "ShrugPrompter": ShrugPrompter,
    "ShrugResponseParser": ShrugResponseParser,
    "PromptTemplateLoader_Shrug": PromptTemplateLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ShrugProviderSelector": "Provider Selector (Shrug)",
    "ShrugPrompter": "VLM Prompter (Shrug)",
    "ShrugResponseParser": "Response Parser (Shrug)",
    "PromptTemplateLoader_Shrug": "Prompt Template Loader (Shrug)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# --- Web Server Endpoints ---
# This section adds a web endpoint to the ComfyUI server that the
# frontend JavaScript uses to fetch dynamic data.

try:
    from aiohttp import web
    from server import PromptServer

    try:
        from .utils import get_models
    except ImportError:
        from utils import get_models

    @PromptServer.instance.routes.get("/shrug/get_models")
    async def get_shrug_models_endpoint(request):
        """
        Handles GET requests to fetch the model list for a given provider.
        Expected query parameters: provider, api_key, base_url.
        """
        provider = request.query.get("provider")
        api_key = request.query.get("api_key")
        base_url = request.query.get("base_url")

        if not provider:
            return web.json_response({"error": "provider parameter is required"}, status=400)
        try:
            models = get_models(provider, api_key, base_url)
            return web.json_response(models)
        except Exception as e:
            print(f"ERROR in /shrug/get_models endpoint: {e}")
            return web.json_response({"error": str(e)}, status=500)

    print("--- Shrug Prompter nodes loaded with web endpoints ---")

except ImportError as e:
    print(f"Warning: Could not import ComfyUI server components: {e}")
    print("API endpoint for Shrug Prompter not available.")
    print("--- Shrug Prompter nodes loaded (standalone mode) ---")
