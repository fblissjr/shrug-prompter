# universal_vlm_prompter.py
# Purpose: This is the primary interface to our backend server.
# It handles all communication, taking ComfyUI inputs (images, masks, text),
# packaging them into a single API request, sending it, and then parsing the response.
# It supports three main use cases:
#   1. Prompt Optimization: Sending images/text and receiving an optimized text prompt.
#   2. Object Detection: Sending an image/text and receiving a mask of a detected object.
#   3. Text-Only Prompting: Sending only text for generation.

import base64
import io
import json
import requests
import numpy as np
import torch
from PIL import Image

class UniversalVLMPrompter:
    @classmethod
    def INPUT_TYPES(cls):
        # Defines the node's inputs. 'images' and 'mask' are optional to allow
        # for text-only use cases.
        return {
            "required": {
                "server_address": ("STRING", {"default": "http://127.0.0.1:8080"}),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 256}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0}),
            },
            "optional": {
                "images": ("IMAGE",),
                "mask": ("MASK",),
            },
        }

    RETURN_TYPES = ("STRING", "MASK", "STRING")
    RETURN_NAMES = ("OPTIMIZED_PROMPT", "DETECTED_MASK", "DETECTED_LABEL")
    FUNCTION = "process_request"
    CATEGORY = "Shrug Nodes/Logic"

    def _tensors_to_base64_list(self, tensor_batch):
        # Why: The server API expects images as Base64-encoded strings.
        # This function converts a batch of ComfyUI's image tensors into this format.
        if tensor_batch is None: return []

        b64_list = []
        for i in range(tensor_batch.shape[0]):
            tensor = tensor_batch[i]
            image_np = tensor.cpu().numpy()
            if image_np.ndim == 4: image_np = image_np[0]
            if image_np.shape[0] in [1, 3]: image_np = np.transpose(image_np, (1, 2, 0))

            image_np = (image_np.squeeze() * 255).astype(np.uint8)
            pil_image = Image.fromarray(image_np)

            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            b64_list.append(f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}")

        return b64_list

    def process_request(self, server_address, system_prompt, user_prompt, max_tokens, temperature, top_p, images=None, mask=None):
        # Why: This is the main execution function for the node.
        endpoint = f"{server_address.strip('/')}/v1/chat/completions"

        # We need the original image dimensions to create a mask from coordinates later.
        if images is not None:
            _ , original_height, original_width, _ = images.shape
        else:
            original_height, original_width = 512, 512 # A default if no image is provided

        image_b64_list = self._tensors_to_base64_list(images)
        mask_b64 = self._tensors_to_base64_list(mask)[0] if mask is not None else None

        # Why: Construct the JSON payload in the OpenAI-compatible format that our server expects.
        content = [{"type": "text", "text": user_prompt}]
        for img_b64 in image_b64_list:
            content.append({"type": "image_url", "image_url": {"url": img_b64}})

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": content}]
        payload = {"messages": messages, "max_tokens": max_tokens, "temperature": temperature, "top_p": top_p, "stream": False}
        if mask_b64: payload["mask"] = mask_b64

        try:
            response = requests.post(endpoint, json=payload, timeout=240)
            response.raise_for_status()
            data = response.json()
            response_text = data["choices"][0]["message"]["content"]

            # Why: This logic makes the node "smart". It tries to parse the server's response as JSON.
            # If it succeeds and finds 'box' and 'label' keys, it assumes an object was detected
            # and outputs a MASK. Otherwise, it assumes the response is a regular text prompt.
            try:
                detection_data = json.loads(response_text)
                if isinstance(detection_data, dict) and "box" in detection_data and "label" in detection_data:
                    box = detection_data["box"]; label = detection_data["label"]
                    x1, y1, x2, y2 = map(int, box)
                    mask_tensor = torch.zeros((1, original_height, original_width), dtype=torch.float32)
                    mask_tensor[:, y1:y2, x1:x2] = 1.0
                    return ("", mask_tensor, label) # Return mask and label, empty the prompt
            except (json.JSONDecodeError, TypeError, KeyError):
                # If parsing fails, it's just a regular text prompt.
                empty_mask = torch.zeros((1, original_height, original_width), dtype=torch.float32)
                return (response_text, empty_mask, "")

        except requests.exceptions.RequestException as e:
            error_message = f"ERROR: Server connection failed: {e}"
            print(error_message)
            return (error_message, torch.zeros((1, 64, 64)), "")
        except Exception as e:
            error_message = f"ERROR: An error occurred: {e}\nResponse: {response.text if 'response' in locals() else 'N/A'}"
            print(error_message)
            return (error_message, torch.zeros((1, 64, 64)), "")
