# shrug-prompter/nodes/response_parser.py

import torch
import json
from typing import Any, List, Tuple

class ShrugResponseParser:
    """
    Parses a VLM response. In list-producing modes, it now outputs a
    single JSON string to ensure maximum compatibility with other custom nodes.
    """
    # WHY: We are back to outputting single items. The first output will be a
    # string that happens to contain a JSON array.
    OUTPUT_IS_LIST = (False, False, False, False)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"context": ("*",)},
            "optional": {
                "original_image": ("IMAGE",),
                "mask_size": ("INT", {"default": 256}),
                "confidence_threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("OPTIMIZED_PROMPT", "DETECTED_MASK", "DETECTED_LABEL", "DEBUG_INFO")
    FUNCTION = "parse_response"
    CATEGORY = "Shrug Nodes/Parsing"

    def parse_response(self, context, original_image=None, mask_size=256,
                      confidence_threshold=0.5, debug_mode=False):

        debug_info = []

        # This part remains the same: get the response and handle errors.
        llm_response = context.get("llm_response")
        if not llm_response:
            return ("ERROR: No llm_response in context", self._create_empty_mask(mask_size,mask_size), "", "ERROR: No llm_response in context")
        if isinstance(llm_response, dict) and "error" in llm_response:
            error_msg = llm_response["error"].get("message", "Unknown error")
            return (f"ERROR: {error_msg}", self._create_empty_mask(mask_size,mask_size), "", f"ERROR: {error_msg}")

        # WHY: We extract the raw text content, which might be a JSON array string
        # or a single prompt, and simply return it as is.
        response_text = self._extract_response_text(llm_response).strip()
        if debug_mode:
            debug_info.append("--- Response Parser ---")
            debug_info.append(f"Raw VLM Response: {response_text[:500]}...")

        # The node's job is now much simpler. It just outputs the text.
        # The new JSONStringToList node will handle the list conversion.
        return (response_text, self._create_empty_mask(mask_size, mask_size), "", "\n".join(debug_info))

    def _extract_response_text(self, resp: Any) -> str:
        """Robustly extracts text content from various VLM response formats."""
        if isinstance(resp, str): return resp
        if not isinstance(resp, dict): return str(resp)
        # Handle standard OpenAI format
        choices = resp.get("choices", [])
        if choices and choices[0].get("message"):
            content = choices[0]["message"].get("content", "")
            # Clean markdown for JSON
            if content.strip().startswith("```json"):
                content = content.strip()[7:-3].strip()
            return content
        # Fallback for other formats
        for key in ["content", "text", "response", "output"]:
            if key in resp: return resp[key]
        return json.dumps(resp)

    def _unpack_json_array(self, text: str, debug_info: list, debug: bool) -> list:
        # WHY: This helper is specifically for the 'json_array' mode. It's robust
        # against common VLM quirks like wrapping JSON in markdown blocks.
        if text.strip().startswith("```json"): text = text.strip()[7:-3].strip()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                if debug: debug_info.append(f"✓ Parsed JSON array with {len(data)} items.")
                return data
            if isinstance(data, dict) and len(data) == 1 and isinstance(next(iter(data.values())), list):
                if debug: debug_info.append(f"✓ Extracted list from JSON object: {len(next(iter(data.values())))} items.")
                return next(iter(data.values()))
            if debug: debug_info.append("⚠️ VLM returned a JSON object, not an array. Using as single item.")
            return [data] # It's valid JSON, but not a list.
        except Exception as e:
            if debug: debug_info.append(f"✗ FAILED to parse JSON array: {e}. Returning raw text.")
            return [text]

    def _parse_single_item(self, item: Any, h: int, w: int, thresh: float, dbg_info: list, dbg: bool) -> tuple:
        # WHY: This function now simplifies the output logic. The main `OPTIMIZED_PROMPT`
        # is ALWAYS the string version of the item. This is predictable. It will
        # *also* try to create a MASK if the item is a valid detection, providing
        # extra utility without complicating the primary output.
        prompt_text = json.dumps(item, indent=2) if isinstance(item, dict) else str(item)
        if dbg: dbg_info.append(f"  - Item Content: {prompt_text[:150]}...")

        mask = self._create_empty_mask(h, w)
        label = ""
        if isinstance(item, dict) and "box" in item:
            box, l, conf = item.get("box",[]), item.get("label","?"), item.get("confidence",1.0)
            if conf >= thresh and len(box) == 4:
                mask = self._create_detection_mask(box, box, box, box, h, w)
                label = f"{l} ({conf:.2f})"
                if dbg: dbg_info.append(f"  - Parsed as valid detection for '{label}' and created mask.")

        return (prompt_text, mask, label)

    def _create_error_list(self, msg: str, dbg_info: list, dbg_mode: bool) -> tuple:
        if dbg_mode: dbg_info.append(f"ERROR: {msg}")
        return ([msg], [self._create_empty_mask(256, 256)], [""], ["\n".join(dbg_info)])

    def _create_empty_mask(self, h: int, w: int) -> torch.Tensor:
        return torch.zeros((1, h, w), dtype=torch.float32, device="cpu")

    def _create_detection_mask(self, x1, y1, x2, y2, h, w) -> torch.Tensor:
        mask = self._create_empty_mask(h, w)
        if x2 > x1 and y2 > y1:
            mask[:, int(y1):int(y2), int(x1):int(x2)] = 1.0
        return mask

class ShrugMaskUtilities:
    """
    Utility node for advanced mask operations and transformations.
    Part of the unified shrug-prompter system.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "operation": (["resize", "crop", "dilate", "erode", "combine"], {"default": "resize"}),
            },
            "optional": {
                "target_size": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "additional_mask": ("MASK",),
                "kernel_size": ("INT", {"default": 3, "min": 1, "max": 15}),
            },
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("processed_mask", "info")
    FUNCTION = "process_mask"
    CATEGORY = "Shrug Nodes/Utilities"

    def process_mask(self, mask, operation, target_size=512, additional_mask=None, kernel_size=3):
        """Process mask with various operations."""

        info = []

        try:
            if operation == "resize":
                result_mask = self._resize_mask(mask, target_size)
                info.append(f"Resized mask to {target_size}x{target_size}")

            elif operation == "crop":
                result_mask = self._crop_mask(mask)
                info.append("Cropped mask to bounding box")

            elif operation == "dilate":
                result_mask = self._dilate_mask(mask, kernel_size)
                info.append(f"Dilated mask with kernel size {kernel_size}")

            elif operation == "erode":
                result_mask = self._erode_mask(mask, kernel_size)
                info.append(f"Eroded mask with kernel size {kernel_size}")

            elif operation == "combine":
                if additional_mask is not None:
                    result_mask = self._combine_masks(mask, additional_mask)
                    info.append("Combined two masks")
                else:
                    result_mask = mask
                    info.append("No additional mask provided for combine operation")

            else:
                result_mask = mask
                info.append(f"Unknown operation: {operation}")

            return (result_mask, "\n".join(info))

        except Exception as e:
            info.append(f"Error in {operation}: {e}")
            return (mask, "\n".join(info))

    def _resize_mask(self, mask: torch.Tensor, target_size: int) -> torch.Tensor:
        """Resize mask to target size."""
        import torch.nn.functional as F

        # Get current size
        _, h, w = mask.shape

        if h == target_size and w == target_size:
            return mask

        # Resize using nearest neighbor to preserve binary values
        resized = F.interpolate(
            mask.unsqueeze(0),  # Add batch dimension
            size=(target_size, target_size),
            mode='nearest'
        ).squeeze(0)  # Remove batch dimension

        return resized

    def _crop_mask(self, mask: torch.Tensor) -> torch.Tensor:
        """Crop mask to its bounding box."""
        # Find bounding box of non-zero values
        nonzero_indices = torch.nonzero(mask.squeeze())

        if len(nonzero_indices) == 0:
            return mask  # Empty mask, return as-is

        min_y, min_x = nonzero_indices.min(dim=0)[0]
        max_y, max_x = nonzero_indices.max(dim=0)[0]

        # Crop to bounding box
        cropped = mask[:, min_y:max_y+1, min_x:max_x+1]

        return cropped

    def _dilate_mask(self, mask: torch.Tensor, kernel_size: int) -> torch.Tensor:
        """Dilate mask using morphological operation."""
        import torch.nn.functional as F

        # Create dilation kernel
        kernel = torch.ones(1, 1, kernel_size, kernel_size)

        # Apply dilation using convolution
        dilated = F.conv2d(
            mask.unsqueeze(0),  # Add batch and channel dimensions
            kernel,
            padding=kernel_size // 2
        ).squeeze(0)  # Remove batch and channel dimensions

        # Clamp to binary values
        dilated = (dilated > 0).float()

        return dilated

    def _erode_mask(self, mask: torch.Tensor, kernel_size: int) -> torch.Tensor:
        """Erode mask using morphological operation."""
        import torch.nn.functional as F

        # Create erosion kernel
        kernel = torch.ones(1, 1, kernel_size, kernel_size)

        # Apply erosion by checking if all kernel values match
        eroded = F.conv2d(
            mask.unsqueeze(0),  # Add batch and channel dimensions
            kernel,
            padding=kernel_size // 2
        ).squeeze(0)  # Remove batch and channel dimensions

        # Erosion: only keep pixels where all kernel positions were 1
        kernel_sum = kernel_size * kernel_size
        eroded = (eroded == kernel_sum).float()

        return eroded

    def _combine_masks(self, mask1: torch.Tensor, mask2: torch.Tensor) -> torch.Tensor:
        """Combine two masks using logical OR."""
        # Ensure same dimensions
        if mask1.shape != mask2.shape:
            # Resize mask2 to match mask1
            mask2_resized = self._resize_mask(mask2, mask1.shape[-1])
            return torch.clamp(mask1 + mask2_resized, 0, 1)

        return torch.clamp(mask1 + mask2, 0, 1)

class JSONStringToList:
    """
    A utility node that parses a JSON-formatted string into a ComfyUI list.
    This is used to explicitly convert the output of a VLM into a list that
    looping nodes can iterate over.
    """
    OUTPUT_IS_LIST = (True,)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("LIST",)
    FUNCTION = "convert_to_list"
    CATEGORY = "Shrug Nodes/Utilities"

    def convert_to_list(self, json_string: str):
        try:
            # WHY: This safely parses the string into a Python list object.
            data = json.loads(json_string)
            if not isinstance(data, list):
                # If the VLM returned a single item instead of a list, wrap it.
                return ([data],)
            return (data,)
        except Exception as e:
            print(f"ERROR: Could not parse JSON string to list: {e}")
            # Return a list containing the original string and the error for debugging.
            return ( [f"JSON PARSE ERROR: {e}", json_string], )
