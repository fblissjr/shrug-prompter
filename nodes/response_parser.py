# In shrug-prompter/nodes/response_parser.py
# Enhanced version with robust None handling for WanVideoWrapper compatibility

import torch
import json
from typing import Any, List, Tuple

class ShrugResponseParser:
    """
    Parses the raw text output from the ShrugPrompter. Its primary job is to
    pass through the VLM's response as a single, clean string. This string can
    then be explicitly handled by other nodes (like JSON String to List).
    
    Enhanced version with robust None handling for WanVideoWrapper compatibility.
    """
    # This node outputs single items. The list conversion is handled by the dedicated utility node.
    OUTPUT_IS_LIST = (False, False, False, False)

    @classmethod
    def INPUT_TYPES(cls):
        # WHY: The problematic widgets (output_format, list_delimiter) have been removed.
        # This makes the node simpler and permanently fixes the bug caused by loading
        # old workflow data into a node with a different widget order.
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
        if isinstance(debug_info, list) and debug_info:
            debug_info = debug_info[0].splitlines()

        llm_response = context.get("llm_response")

        # ENHANCED: Provide fallback prompt if no LLM response
        if not llm_response:
            fallback_prompt = "A cinematic scene with dynamic camera movement, professional lighting, and compelling visual storytelling"
            debug_info.append("WARNING: No llm_response in context, using fallback prompt")
            return (fallback_prompt, self._create_empty_mask(mask_size, mask_size), "", "WARNING: No llm_response in context")

        response_text = self._extract_response_text(llm_response).strip()
        if debug_mode:
            debug_info.append(f"--- Response Parser ---\nRaw VLM Response: {response_text[:500]}...")

        # ENHANCED: Ensure we never return None or empty string
        if not response_text or response_text.strip() == "":
            fallback_prompt = "A cinematic scene with dynamic camera movement, professional lighting, and compelling visual storytelling"
            debug_info.append("WARNING: Empty response text, using fallback prompt")
            response_text = fallback_prompt

        # ENHANCED: Additional safety check for specific error patterns
        if response_text.startswith("ERROR:") or response_text.startswith("PARSE ERROR:"):
            fallback_prompt = "A cinematic scene with dynamic camera movement, professional lighting, and compelling visual storytelling"
            debug_info.append(f"WARNING: Error in response ({response_text[:50]}), using fallback prompt")
            response_text = fallback_prompt

        mask, label = self._try_parse_detection(response_text, original_image, mask_size, confidence_threshold)

        # FINAL SAFETY CHECK: Ensure response_text is never None
        if response_text is None:
            response_text = "A cinematic scene with dynamic camera movement, professional lighting, and compelling visual storytelling"
            debug_info.append("CRITICAL: response_text was None, using fallback prompt")

        return (response_text, mask, label, "\n".join(debug_info))

    def _extract_response_text(self, resp: Any) -> str:
        """Robustly extracts text content from various VLM response formats."""
        if isinstance(resp, str): 
            return resp if resp else "A cinematic scene with dynamic camera movement and professional lighting"
        if not isinstance(resp, dict): 
            return str(resp) if resp else "A cinematic scene with dynamic camera movement and professional lighting"
        choices = resp.get("choices", [])
        if choices and "message" in choices[0] and "content" in choices[0]["message"]:
            content = choices[0]["message"]["content"]
            if content and content.strip().startswith("```json"):
                content = content.strip()[7:-3].strip()
            return content if content else "A cinematic scene with dynamic camera movement and professional lighting"
        for key in ["content", "text", "response", "output"]:
            if key in resp and resp[key]: 
                return resp[key]
        # Last resort: return JSON dump or fallback
        try:
            result = json.dumps(resp)
            return result if result else "A cinematic scene with dynamic camera movement and professional lighting"
        except:
            return "A cinematic scene with dynamic camera movement and professional lighting"

    def _try_parse_detection(self, text: str, image: torch.Tensor, size: int, thresh: float) -> Tuple[torch.Tensor, str]:
        """Tries to create a mask if the text is a detection JSON, otherwise returns empty."""
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "box" in data and "label" in data:
                h, w = (image.shape, image.shape) if image is not None else (size, size)
                box, label, conf = data.get("box",[]), data.get("label","?"), data.get("confidence",1.0)
                if conf >= thresh and len(box) == 4:
                    mask = self._create_detection_mask(box, h, w)
                    return (mask, f"{label} ({conf:.2f})")
        except:
            pass
        return (self._create_empty_mask(size, size), "")

    def _create_empty_mask(self, h: int, w: int) -> torch.Tensor:
        return torch.zeros((1, h, w), dtype=torch.float32, device="cpu")

    def _create_detection_mask(self, box: list, h: int, w: int) -> torch.Tensor:
        mask = self._create_empty_mask(h, w)
        x1, y1, x2, y2 = map(int, box)
        if x2 > x1 and y2 > y1:
            mask[:, y1:y2, x1:x2] = 1.0
        return mask


class JSONStringToList:
    """
    Utility node to parse a JSON string into a ComfyUI list.
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
