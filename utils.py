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
        if not api_key:
            print("Warning: Cannot fetch OpenAI models; API key is missing.")
            return ["API key required"]

        endpoint = f"{base_url.strip('/')}/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Filter the model list for relevant chat/completion models.
            models = sorted([
                m["id"] for m in data.get("data", [])
                if "gpt" in m["id"] and "internal" not in m["id"]
            ])
            return models if models else ["No compatible models found"]
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to fetch OpenAI models. Details: {e}")
            return ["Error fetching models"]
    else:
        return [f"Model fetching not implemented for '{provider}'."]

def tensors_to_base64_list(tensor_batch):
    """Converts a ComfyUI IMAGE or MASK tensor batch to a list of Base64 strings."""
    if tensor_batch is None:
        return []

    b64_list = []
    for i in range(tensor_batch.shape[0]):
        tensor = tensor_batch[i]
        image_np = tensor.cpu().numpy()

        if image_np.ndim == 3 and image_np.shape[0] in [1, 3, 4]:
             image_np = np.transpose(image_np, (1, 2, 0))

        image_np = (image_np.squeeze() * 255).astype(np.uint8)

        if image_np.ndim == 2: mode = 'L'
        elif image_np.shape[2] == 3: mode = 'RGB'
        else: mode = 'RGBA'

        pil_image = Image.fromarray(image_np, mode=mode)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        b64_list.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))
    return b64_list

def run_async(coro):
    """Runs an async coroutine from a synchronous context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
