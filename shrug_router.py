# In shrug-prompter/shrug_router.py
try:
    # Try relative import first (for ComfyUI)
    try:
        # Try sync version first (avoids event loop issues)
        from .api.openai_api_sync import send_request_openai
    except ImportError:
        try:
            # Try fixed version
            from .api.openai_api_fixed import send_request_openai
        except ImportError:
            try:
                # Use optimized version if available
                from .api.openai_api_optimized import send_request_openai
            except ImportError:
                # Fallback to standard version
                from .api.openai_api import send_request_openai
except ImportError:
    # Fallback to absolute import (for standalone testing)
    try:
        from api.openai_api_sync import send_request_openai
    except ImportError:
        try:
            from api.openai_api_fixed import send_request_openai
        except ImportError:
            try:
                from api.openai_api_optimized import send_request_openai
            except ImportError:
                from api.openai_api import send_request_openai

# As new providers are added, their API modules will be imported here.
# e.g., from .api.gemini_api import send_request_gemini

def send_request(provider: str, **kwargs):
    """
    Routes the request to the correct provider-specific API module based on the
    'provider' string.

    Args:
        provider (str): The name of the LLM provider (e.g., "openai").
        **kwargs: A dictionary of arguments to be passed to the provider's
                  request function.

    Returns:
        The JSON response from the specified API provider.
    """
    provider_lower = provider.lower()

    # The router dispatches the call to the appropriate module.
    if provider_lower == "openai":
        # Remove 'provider' key as it's for routing only
        kwargs.pop('provider', None)

        # Ensure required parameters are present
        required_params = ['messages', 'api_key', 'base_url', 'llm_model', 'max_tokens', 'temperature', 'top_p']
        missing_params = [param for param in required_params if param not in kwargs]

        if missing_params:
            return {"error": {"message": f"Missing required parameters: {missing_params}"}}

        return send_request_openai(**kwargs)

    # Example of future expansion:
    # elif provider_lower == "gemini":
    #     kwargs.pop('provider', None)
    #     return await send_request_gemini(**kwargs)

    else:
        return {"error": {"message": f"Provider '{provider}' is not supported in the router."}}
