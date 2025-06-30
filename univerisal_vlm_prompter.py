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
        return {
            "required": {
                "server_address": ("STRING", {"default": "http://127.0.0.1:8080"}),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 512, "min": 32, "max": 99999}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.1}),
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
        if tensor_batch is None:
            return []

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

    # CORRECTED arugment name from 'image' to 'images'
    def process_request(self, server_address, system_prompt, user_prompt, max_tokens, temperature, top_p, images=None, mask=None):
        endpoint = f"{server_address.strip('/')}/v1/chat/completions"

        if images is None:
            original_height, original_width = 512, 512
        else:
            _ , original_height, original_width, _ = images.shape

        image_b64_list = self._tensors_to_base64_list(images)
        mask_b64 = self._tensors_to_base64_list(mask)[0] if mask is not None else None

        content = [{"type": "text", "text": user_prompt}]
        for img_b64 in image_b64_list:
            content.append({"type": "image_url", "image_url": {"url": img_b64}})

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

        payload = { "messages": messages, "max_tokens": max_tokens, "temperature": temperature, "top_p": top_p, "stream": False }
        if mask_b64: payload["mask"] = mask_b64

        try:
            response = requests.post(endpoint, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            response_text = data["choices"][0]["message"]["content"]

            try:
                detection_data = json.loads(response_text)
                if isinstance(detection_data, dict) and "box" in detection_data and "label" in detection_data:
                    box = detection_data["box"]; label = detection_data["label"]
                    x1, y1, x2, y2 = map(int, box)
                    mask_tensor = torch.zeros((1, original_height, original_width), dtype=torch.float32)
                    mask_tensor[:, y1:y2, x1:x2] = 1.0
                    return ("", mask_tensor, label)
            except (json.JSONDecodeError, TypeError, KeyError):
                empty_mask = torch.zeros((1, original_height, original_width), dtype=torch.float32)
                return (response_text, empty_mask, "")

        except requests.exceptions.RequestException as e:
            return (f"ERROR: Server connection failed: {e}", torch.zeros((1, 64, 64)), "")
        except Exception as e:
            return (f"ERROR: {e}\nResponse: {response.text if 'response' in locals() else 'N/A'}", torch.zeros((1, 64, 64)), "")
