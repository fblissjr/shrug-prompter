# nodes/provider_selector.py
# In shrug-prompter/nodes/provider_selector.py
import os

class ShrugProviderSelector:
    """
    A configuration node to collect API credentials and model specifications.
    It packages these settings into a 'context' dictionary for downstream nodes.
    """
    PROVIDERS = ["openai"] # This list can be expanded as more providers are supported.

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (cls.PROVIDERS, {"default": "openai"}),
                # Defaults are read from environment variables for convenience,
                # but can be overridden in the UI.
                "base_url": ("STRING", {
                    "multiline": False,
                    "default": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": os.environ.get("OPENAI_API_KEY", "")
                }),
                # This widget is a placeholder. The accompanying javascript file
                # will replace it with a dynamic COMBO box at runtime.
                "llm_model": ("STRING", {"default": "Select a provider to fetch models"}),
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("context",)
    FUNCTION = "create_context"
    CATEGORY = "Shrug Nodes/Config"

    def create_context(self, provider, base_url, api_key, llm_model):
        """
        Validates inputs and packages them into a provider_config dictionary.
        Prioritizes user-provided widget values over environment variables.
        """
        # If the api_key widget is empty, fall back to the environment variable.
        final_api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")

        if not final_api_key and provider != "ollama": # Ollama doesn't require a key
             print(f"Warning: ShrugProviderSelector - API Key for {provider} is not set.")

        context = {
            "provider_config": {
                "provider": provider,
                "base_url": base_url,
                "api_key": final_api_key,
                "llm_model": llm_model,
            }
        }
        # The output must be a tuple.
        return (context,)
