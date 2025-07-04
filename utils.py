# In shrug-prompter/utils.py
import os
import requests
import base64
import io
import asyncio
import numpy as np
import torch
from PIL import Image

def get_models(provider, api_key, base_url):
    """Fetches the list of available models for a given provider via its API."""
    provider_lower = provider.lower()

    if provider_lower == "openai":
        # Handle both OpenAI and edge-llm servers
        endpoint = f"{base_url.strip('/')}/v1/models"

        # Only require API key for actual OpenAI, not for local servers
        headers = {}
        if api_key and not ("localhost" in base_url or "127.0.0.1" in base_url or "0.0.0.0" in base_url):
            headers["Authorization"] = f"Bearer {api_key}"
        elif api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = requests.get(endpoint, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Extract model IDs from the response
            if "data" in data and isinstance(data["data"], list):
                # OpenAI/edge-llm format
                models = []
                for model in data["data"]:
                    if isinstance(model, dict) and "id" in model:
                        model_id = model["id"]
                        # Add vision indicator if available
                        vision_indicator = ""
                        if model.get("vision", False):
                            vision_indicator = " (Vision)"
                        models.append(f"{model_id}{vision_indicator}")

                # Sort models, put vision models first
                models.sort(key=lambda x: (not x.endswith("(Vision)"), x.lower()))
                return models if models else ["No models found"]
            else:
                # Fallback: try to extract model names from various formats
                model_list = data if isinstance(data, list) else []
                return model_list if model_list else ["Unexpected response format"]

        except requests.exceptions.Timeout:
            print(f"WARNING: Timeout fetching models from {base_url}")
            return ["Timeout - check server"]
        except requests.exceptions.ConnectionError:
            print(f"WARNING: Cannot connect to {base_url}")
            return ["Connection failed"]
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to fetch models from {base_url}. Details: {e}")
            return ["Error fetching models"]
        except Exception as e:
            print(f"ERROR: Unexpected error fetching models: {e}")
            return ["Unexpected error"]
    else:
        return [f"Model fetching not implemented for '{provider}'."]

def tensors_to_base64_list(tensor_batch):
    """Converts a ComfyUI IMAGE or MASK tensor batch to a list of Base64 strings."""
    if tensor_batch is None:
        return []

    b64_list = []
    try:
        for i in range(tensor_batch.shape[0]):
            tensor = tensor_batch[i]
            image_np = tensor.cpu().numpy()

            # Handle different tensor formats (ComfyUI uses HWC format)
            if image_np.ndim == 3:
                # If channels are first (CHW), transpose to HWC
                if image_np.shape[0] in [1, 3, 4] and image_np.shape[0] < min(image_np.shape[1:]):
                    image_np = np.transpose(image_np, (1, 2, 0))

            # Ensure values are in 0-255 range
            if image_np.max() <= 1.0:
                image_np = (image_np * 255).astype(np.uint8)
            else:
                image_np = np.clip(image_np, 0, 255).astype(np.uint8)

            # Remove extra dimensions
            image_np = image_np.squeeze()

            # Determine PIL mode
            if image_np.ndim == 2:
                mode = 'L'  # Grayscale
            elif image_np.ndim == 3:
                if image_np.shape[2] == 1:
                    image_np = image_np.squeeze(axis=2)
                    mode = 'L'
                elif image_np.shape[2] == 3:
                    mode = 'RGB'
                elif image_np.shape[2] == 4:
                    mode = 'RGBA'
                else:
                    # Fallback: take first 3 channels
                    image_np = image_np[:, :, :3]
                    mode = 'RGB'
            else:
                raise ValueError(f"Unsupported image shape: {image_np.shape}")

            # Create PIL image and convert to base64
            pil_image = Image.fromarray(image_np, mode=mode)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            b64_encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
            b64_list.append(b64_encoded)

    except Exception as e:
        print(f"ERROR: Failed to convert tensor to base64: {e}")
        print(f"Tensor shape: {tensor_batch.shape if tensor_batch is not None else 'None'}")
        return []

    return b64_list

def run_async(coro):
    """Runs an async coroutine from a synchronous context."""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(coro)
