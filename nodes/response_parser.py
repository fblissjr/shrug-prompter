# In shrug-prompter/nodes/response_parser.py
# Final, corrected, and complete version.

import torch
import json
from typing import Any, List, Tuple

class ShrugResponseParser:
    """
    Parses the raw text output from the ShrugPrompter. Its primary job is to
    pass through the VLM's response as a single, clean string.
    """
    OUTPUT_IS_LIST = (False, False, False, False)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"context": ("*",)},
            "optional": {
                "original_image": ("IMAGE",),
                "mask_size": ("INT", {"default": 256, "min": 64, "max": 2048}),
                "confidence_threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("OPTIMIZED_PROMPT", "DETECTED_MASK", "DETECTED_LABEL", "DEBUG_INFO")
    FUNCTION = "parse_response"
    CATEGORY = "Shrug Nodes/Parsing"

    def parse_response(self, context, original_image=None, mask_size=256, confidence_threshold=0.5, debug_mode=False):
        debug_info = context.get("debug_info", [])
        llm_response = context.get("llm_response")

        if not llm_response:
            return ("ERROR: No llm_response in context", self._create_empty_mask(mask_size,mask_size), "", "ERROR: No llm_response in context")

        response_text = self._extract_response_text(llm_response).strip()
        if debug_mode:
            debug_info.append(f"Raw VLM Response: {response_text[:500]}...")

        mask, label = self._try_parse_detection(response_text, original_image, mask_size, confidence_threshold)

        return (response_text, mask, label, "\n".join(debug_info))

    def _extract_response_text(self, resp: Any) -> str:
        if isinstance(resp, str): return resp
        if not isinstance(resp, dict): return str(resp)
        choices = resp.get("choices", [])
        if choices and "message" in choices[0] and "content" in choices[0]["message"]:
            content = choices[0]["message"]["content"]
            if content.strip().startswith("```json"):
                content = content.strip()[7:-3].strip()
            return content
        for key in ["content", "text", "response", "output"]:
            if key in resp: return resp[key]
        return json.dumps(resp)

    def _try_parse_detection(self, text: str, image: torch.Tensor, size: int, thresh: float) -> Tuple[torch.Tensor, str]:
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "box" in data and "label" in data:
                h, w = (image.shape, image.shape) if image is not None else (size, size)
                box, label, conf = data.get("box",[]), data.get("label","?"), data.get("confidence",1.0)
                if conf >= thresh and len(box) == 4:
                    mask = self._create_detection_mask(box, box, box, box, h, w)
                    return (mask, f"{label} ({conf:.2f})")
        except:
            pass
        return (self._create_empty_mask(size, size), "")

    def _create_empty_mask(self, h: int, w: int) -> torch.Tensor:
        return torch.zeros((1, h, w), dtype=torch.float32, device="cpu")

    def _create_detection_mask(self, x1, y1, x2, y2, h, w) -> torch.Tensor:
        mask = self._create_empty_mask(h, w)
        if x2 > x1 and y2 > y1:
            mask[:, int(y1):int(y2), int(x1):int(x2)] = 1.0
        return mask

class JSONStringToList:
    """
    Utility node to parse a JSON string into a ComfyUI list, making it compatible
    with looping nodes. This provides an explicit and robust conversion step.
    """
    OUTPUT_IS_LIST = (True,)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"json_string": ("STRING", {"multiline": True})}}

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("LIST",)
    FUNCTION = "convert_to_list"
    CATEGORY = "Shrug Nodes/Utilities"

    def convert_to_list(self, json_string: str):
        try:
            data = json.loads(json_string)
            if not isinstance(data, list):
                return ([data],)
            return (data,)
        except Exception as e:
            print(f"ERROR: Could not parse JSON string to list: {e}")
            return ([f"JSON PARSE ERROR: {e}", json_string],)
