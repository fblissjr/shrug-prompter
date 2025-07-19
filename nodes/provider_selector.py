# nodes/provider_selector.py
# In shrug-prompter/nodes/provider_selector.py
import os

class ShrugProviderSelector:
    """
    A configuration node to pass API credentials and model specifications.
    It packages these settings into a 'context' dictionary for downstream nodes.
    """
    PROVIDERS = ["openai"]  # This list can be expanded as more providers are supported.

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (cls.PROVIDERS, {"default": "openai"}),
                # Set better defaults for local edge-llm server
                "base_url": ("STRING", {
                    "multiline": False,
                    "default": os.environ.get("OPENAI_BASE_URL", "http://localhost:8080")
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": os.environ.get("OPENAI_API_KEY", "not-required-for-local")
                }),
                # This widget allows manual model entry or dropdown selection
                # The JS will try to populate it dynamically, but manual entry always works
                "llm_model": ("STRING", {
                    "default": "Enter model name (will auto-populate if server is reachable)",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("VLM_CONTEXT",)
    RETURN_NAMES = ("context",)
    FUNCTION = "create_context"
    CATEGORY = "Shrug Nodes/Config"

    def create_context(self, provider, base_url, api_key, llm_model):
        """
        Validates inputs and packages them into a provider_config dictionary.
        Prioritizes user-provided widget values over environment variables.
        """
        # Clean up the model name (remove vision indicators that might be added by the UI)
        clean_model = llm_model.replace(" (Vision)", "").strip()

        # For local servers, API key might not be required
        final_api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")

        # Don't warn about missing API key for localhost servers
        is_local = any(host in base_url.lower() for host in ["localhost", "127.0.0.1", "0.0.0.0"])

        if not final_api_key and provider != "ollama" and not is_local:
            print(f"Warning: ShrugProviderSelector - API Key for {provider} is not set.")

        # Ensure base_url has protocol
        if not base_url.startswith(("http://", "https://")):
            base_url = f"http://{base_url}"

        context = {
            "provider_config": {
                "provider": provider,
                "base_url": base_url.rstrip('/'),  # Remove trailing slash
                "api_key": final_api_key,
                "llm_model": clean_model,
            }
        }

        print(f"Provider config: {provider} at {base_url} using model {clean_model}")

        # The output must be a tuple
        return (context,)
