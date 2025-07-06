# shrug-prompter/nodes/response_parser.py

import torch
import json
from typing import Any, List, Tuple

class ShrugResponseParser:
    """
    Parses a VLM response, intelligently unpacking lists for looping workflows
    based on metadata passed in the context. This makes the workflow behavior
    driven by the prompt template itself.
    """
    # WHY: This is the most important declaration. It tells ComfyUI that this node's
    # outputs are lists, which is what allows them to be connected to loopers.
    OUTPUT_IS_LIST = (True, True, True, True)

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

    def parse_response(self, context, original_image=None, mask_size=256, confidence_threshold=0.5, debug_mode=False):

        # WHY: The debug info from the prompter is carried through, so you have a
        # complete log of the VLM call for each item in the loop.
        base_debug_info = context.get("debug_info", [])
        if isinstance(base_debug_info, list) and base_debug_info:
            base_debug_info = base_debug_info[0].splitlines()

        # WHY: The parser now reads the metadata to determine its strategy.
        # This makes its behavior explicit and predictable, driven by the template.
        metadata_str = context.get("vlm_metadata", "{}")
        try: metadata = json.loads(metadata_str)
        except: metadata = {}
        output_type = metadata.get("output_type", "single_string")
        if debug_mode: base_debug_info.append(f"--- Parser --- \nMetadata Strategy: '{output_type}'")

        llm_response = context.get("llm_response")
        if not llm_response: return self._create_error_list("No llm_response in context", base_debug_info, debug_mode)
        if isinstance(llm_response, dict) and "error" in llm_response:
            return self._create_error_list(llm_response["error"].get("message", "Unknown error"), base_debug_info, debug_mode)

        response_text = self._extract_response_text(llm_response).strip()
        if not response_text: return self._create_error_list("VLM returned empty content", base_debug_info, debug_mode)
        if debug_mode: base_debug_info.append(f"Raw Response ({len(response_text)} chars): {response_text[:300]}...")

        # WHY: This is the core logic branch. Based on the template's metadata,
        # it decides whether to treat the response as one item or a list of items.
        results_list = []
        if output_type == "json_array":
            results_list = self._unpack_json_array(response_text, base_debug_info, debug_mode)
        else: # 'single_string' or any other value is treated as one item.
            results_list = [response_text]
            if debug_mode: base_debug_info.append("✓ Treating response as a single item based on metadata.")

        all_prompts, all_masks, all_labels, all_debugs = [], [], [], []
        h, w = (original_image.shape[1], original_image.shape[2]) if original_image is not None else (mask_size, mask_size)

        for i, item in enumerate(results_list):
            item_debug = list(base_debug_info)
            if debug_mode: item_debug.append(f"--- Item {i+1}/{len(results_list)} ---")

            prompt, mask, label = self._parse_single_item(item, h, w, confidence_threshold, item_debug, debug_mode)

            all_prompts.append(prompt)
            all_masks.append(mask)
            all_labels.append(label)
            all_debugs.append("\n".join(item_debug))

        return (all_prompts, all_masks, all_labels, all_debugs)

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

    def _extract_response_text(self, resp: Any) -> str:
        if isinstance(resp, str): return resp
        if not isinstance(resp, dict): return str(resp)
        choices = resp.get("choices", [])
        if choices and choices.get("message"): return choices["message"].get("content", "")
        for key in ["content", "text", "response", "output"]:
            if key in resp: return resp[key]
        return json.dumps(resp)

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
