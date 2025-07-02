# nodes/response_parser.py
import torch
import json

class ShrugResponseParser:
    """
    Parses the `llm_response` from the context. It checks if the response is
    a JSON object matching the object detection schema; otherwise, it passes
    through the response as a text prompt.
    """
    @classmethod
    def INPUT_TYPES(cls):
        # ... (INPUT_TYPES remain the same)
        return {
            "required": {"context": ("*",)},
            "optional": {"original_image": ("IMAGE",)},
        }

    RETURN_TYPES = ("STRING", "MASK", "STRING")
    RETURN_NAMES = ("OPTIMIZED_PROMPT", "DETECTED_MASK", "DETECTED_LABEL")
    FUNCTION = "parse_response"
    CATEGORY = "Shrug Nodes/Parsing"

    def parse_response(self, context, original_image=None):
        llm_response = context.get("llm_response", {})

        # Determine mask dimensions from the original image to ensure alignment.
        if original_image is not None:
            _, height, width, _ = original_image.shape
        else:
            height, width = 512, 512 # Fallback size.

        empty_mask = torch.zeros((1, height, width), dtype=torch.float32, device="cpu")

        if not llm_response or "error" in llm_response:
            error_msg = llm_response.get("error", {}).get("message", "Upstream node error")
            print(f"Error in ShrugResponseParser: {error_msg}")
            return (f"ERROR: {error_msg}", empty_mask, "")

        try:
            response_text = llm_response.get("choices", [{}]).get("message", {}).get("content", "")
        except Exception:
            response_text = ""

        if not response_text:
            return ("ERROR: Received empty content from VLM.", empty_mask, "")

        # Attempt to parse the response as a JSON object for object detection.
        try:
            detection_data = json.loads(response_text)
            if isinstance(detection_data, dict) and "box" in detection_data and "label" in detection_data:
                box = detection_data.get("box",)
                label = detection_data.get("label", "not_found")

                if label == "not_found":
                    return ("Object not found.", empty_mask, label)

                x1, y1, x2, y2 = map(int, box)
                mask_tensor = torch.zeros((1, height, width), dtype=torch.float32, device="cpu")
                mask_tensor[:, y1:y2, x1:x2] = 1.0
                return ("", mask_tensor, label)
        except (json.JSONDecodeError, TypeError):
            # If not a valid detection JSON, pass it through as a text prompt.
            return (response_text, empty_mask, "")
