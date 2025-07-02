# In shrug-prompter/shrug_router.py
from .api.openai_api import send_request_openai
# As new providers are added, their API modules will be imported here.
# e.g., from .api.gemini_api import send_request_gemini

async def send_request(provider: str, **kwargs):
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
        # The 'provider' key is for routing and is not needed by the API module.
        kwargs.pop('provider', None)
        return await send_request_openai(**kwargs)

    # Example of future expansion:
    # elif provider_lower == "gemini":
    #     kwargs.pop('provider', None)
    #     return await send_request_gemini(**kwargs)

    else:
        raise ValueError(f"Provider '{provider}' is not supported in the router.")
