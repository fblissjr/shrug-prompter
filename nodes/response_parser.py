# nodes/response_parser.py

import torch
import json
from typing import Dict, Any, List, Tuple, Optional

class ShrugResponseParser:
    """
    Unified response parser with enhanced parsing, auto-format detection, and debugging.
    Backward compatible with existing workflows.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"context": ("*",)},
            "optional": {
                "original_image": ("IMAGE",),
                "output_format": (["auto", "text", "detection"], {"default": "auto"}),
                "mask_size": ("INT", {"default": 256, "min": 64, "max": 2048}),
                "confidence_threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("OPTIMIZED_PROMPT", "DETECTED_MASK", "DETECTED_LABEL", "DEBUG_INFO")
    FUNCTION = "parse_response"
    CATEGORY = "Shrug Nodes/Parsing"

    def parse_response(self, context, original_image=None, output_format="auto",
                      mask_size=256, confidence_threshold=0.5, debug_mode=False):
        """Parse response with all enhancements and backward compatibility."""

        debug_info = []

        # Extract response from context
        llm_response = context.get("llm_response")
        if not llm_response:
            if debug_mode:
                debug_info.append("ERROR: No llm_response found in context")
            print("Error in ShrugResponseParser: No llm_response found in context")
            return self._create_error_response("No LLM response found", debug_info, debug_mode=debug_mode)

        # Determine dimensions from the original image to ensure alignment
        if original_image is not None:
            _, height, width, _ = original_image.shape
            if debug_mode:
                debug_info.append(f"Using original image dimensions: {width}x{height}")
        else:
            height, width = mask_size, mask_size
            if debug_mode:
                debug_info.append(f"Using fallback dimensions: {width}x{height}")

        # Handle error responses early
        if isinstance(llm_response, dict) and "error" in llm_response:
            error_info = llm_response["error"]
            if isinstance(error_info, dict):
                error_msg = error_info.get("message", "Unknown error from upstream")
            else:
                error_msg = str(error_info)
            if debug_mode:
                debug_info.append(f"Error in response: {error_msg}")
            print(f"Error in ShrugResponseParser: {error_msg}")
            return self._create_error_response(f"ERROR: {error_msg}", debug_info, height, width, debug_mode)

        # Extract response text with robust parsing
        response_text = self._extract_response_text(llm_response, debug_info, debug_mode)

        if not response_text:
            if debug_mode:
                debug_info.append("ERROR: Empty response content")
            print("Error in ShrugResponseParser: Received empty content from VLM.")
            return self._create_error_response("ERROR: Received empty content from VLM.", debug_info, height, width, debug_mode)

        # Clean up response text
        response_text = response_text.strip()
        if debug_mode:
            debug_info.append(f"Extracted text: {len(response_text)} characters")

        # Determine output format
        if output_format == "auto":
            detected_format = self._detect_format(response_text)
            if debug_mode:
                debug_info.append(f"Auto-detected format: {detected_format}")
        else:
            detected_format = output_format
            if debug_mode:
                debug_info.append(f"Using specified format: {detected_format}")

        # Process based on format
        if detected_format == "detection":
            result = self._parse_detection(response_text, height, width, confidence_threshold, debug_info, debug_mode)
            if result:
                if debug_mode:
                    debug_info.append("✓ Successfully parsed detection")
                return result

        # Default to text output
        if debug_mode:
            debug_info.append("→ Returning as optimized prompt")
        empty_mask = self._create_empty_mask(height, width)
        debug_output = "\n".join(debug_info) if debug_mode else ""
        return (response_text, empty_mask, "", debug_output)

    def _extract_response_text(self, llm_response: Any, debug_info: List[str], debug_mode: bool) -> str:
        """Robustly extract text content from various response formats."""
        try:
            # Handle string responses directly
            if isinstance(llm_response, str):
                if debug_mode:
                    debug_info.append("Response format: plain string")
                return llm_response

            # Handle dict responses
            if not isinstance(llm_response, dict):
                if debug_mode:
                    debug_info.append(f"WARNING: Unexpected response type: {type(llm_response)}")
                return str(llm_response)

            if debug_mode:
                debug_info.append("Response format: dictionary")

            # Try OpenAI format first
            choices = llm_response.get("choices", [])
            if choices and len(choices) > 0:
                choice = choices[0]

                if not isinstance(choice, dict):
                    if debug_mode:
                        debug_info.append(f"WARNING: Choice is not a dict: {type(choice)}")
                    return str(choice)

                # Handle different choice formats
                if "message" in choice:
                    # Standard OpenAI format
                    message = choice["message"]
                    if isinstance(message, dict):
                        content = message.get("content", "")
                        if debug_mode:
                            debug_info.append("Extracted from: choices[0].message.content")
                        return content
                    else:
                        return str(message)
                elif "delta" in choice:
                    # Streaming format that got collected
                    delta = choice["delta"]
                    if isinstance(delta, dict):
                        content = delta.get("content", "")
                        if debug_mode:
                            debug_info.append("Extracted from: choices[0].delta.content")
                        return content
                    else:
                        return str(delta)
                elif "text" in choice:
                    # Alternative format
                    if debug_mode:
                        debug_info.append("Extracted from: choices[0].text")
                    return choice["text"]

            # Try alternative response formats
            for key in ["content", "text", "response", "output"]:
                if key in llm_response:
                    if debug_mode:
                        debug_info.append(f"Extracted from: {key}")
                    return llm_response[key]

            if debug_mode:
                debug_info.append(f"WARNING: No recognized content field in response")
            return str(llm_response)

        except Exception as e:
            if debug_mode:
                debug_info.append(f"ERROR extracting response text: {e}")
            print(f"ERROR parsing response: {e}")
            return ""

    def _detect_format(self, response_text: str) -> str:
        """Auto-detect the response format."""
        # Look for JSON patterns
        if '{' in response_text and '}' in response_text:
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}')
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end+1]
                    data = json.loads(json_text)

                    if isinstance(data, dict):
                        # Check for detection format
                        if "box" in data and "label" in data:
                            return "detection"
                        # Check for structured data
                        elif any(key in data for key in ["objects", "detections", "results"]):
                            return "detection"
            except json.JSONDecodeError:
                pass

        return "text"

    def _parse_detection(self, response_text: str, height: int, width: int,
                        confidence_threshold: float, debug_info: List[str], debug_mode: bool) -> Optional[Tuple]:
        """Parse object detection response format."""
        try:
            # Try to find JSON in the response (might have extra text around it)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}')

            if json_start == -1 or json_end == -1 or json_end <= json_start:
                return None

            json_text = response_text[json_start:json_end+1]
            detection_data = json.loads(json_text)

            if not isinstance(detection_data, dict):
                return None

            # Handle single detection
            if "box" in detection_data and "label" in detection_data:
                return self._process_single_detection(detection_data, height, width, confidence_threshold, debug_info, debug_mode)

            # Handle multiple detections
            elif "detections" in detection_data or "objects" in detection_data:
                detections = detection_data.get("detections", detection_data.get("objects", []))
                return self._process_multiple_detections(detections, height, width, confidence_threshold, debug_info, debug_mode)

            return None

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            if debug_mode:
                debug_info.append(f"Detection parsing error: {e}")
            # If not a valid detection JSON, pass it through as a text prompt
            return None

    def _process_single_detection(self, detection_data: Dict, height: int, width: int,
                                 confidence_threshold: float, debug_info: List[str], debug_mode: bool) -> Tuple:
        """Process a single detection."""
        box = detection_data.get("box", [])
        label = detection_data.get("label", "unknown")
        confidence = detection_data.get("confidence", 1.0)

        if confidence < confidence_threshold:
            if debug_mode:
                debug_info.append(f"Detection below confidence threshold: {confidence:.2f} < {confidence_threshold:.2f}")
            empty_mask = self._create_empty_mask(height, width)
            return ("Low confidence detection", empty_mask, f"{label} ({confidence:.2f})")

        if label == "not_found" or not box or len(box) != 4:
            if debug_mode:
                debug_info.append("Object not found or invalid box")
            empty_mask = self._create_empty_mask(height, width)
            return ("Object not found.", empty_mask, label)

        try:
            x1, y1, x2, y2 = map(int, box)
            if debug_mode:
                debug_info.append(f"Detection box: [{x1}, {y1}, {x2}, {y2}]")

            # Ensure coordinates are within image bounds
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(x1, min(x2, width))
            y2 = max(y1, min(y2, height))

            # Create mask tensor
            mask_tensor = self._create_detection_mask(x1, y1, x2, y2, height, width)

            confidence_str = f" ({confidence:.2f})" if confidence < 1.0 else ""
            return ("", mask_tensor, f"{label}{confidence_str}")

        except (ValueError, TypeError) as e:
            if debug_mode:
                debug_info.append(f"ERROR: Invalid box coordinates: {box}, error: {e}")
            print(f"ERROR: Invalid box coordinates: {box}, error: {e}")
            empty_mask = self._create_empty_mask(height, width)
            return (f"ERROR: Invalid detection box: {box}", empty_mask, "")

    def _process_multiple_detections(self, detections: List, height: int, width: int,
                                   confidence_threshold: float, debug_info: List[str], debug_mode: bool) -> Tuple:
        """Process multiple detections and combine masks."""
        if not detections:
            empty_mask = self._create_empty_mask(height, width)
            return ("No detections found", empty_mask, "")

        valid_detections = []
        combined_mask = torch.zeros((1, height, width), dtype=torch.float32, device="cpu")

        for i, detection in enumerate(detections):
            if not isinstance(detection, dict):
                continue

            confidence = detection.get("confidence", 1.0)
            if confidence < confidence_threshold:
                continue

            box = detection.get("box", [])
            label = detection.get("label", f"object_{i}")

            if len(box) == 4:
                try:
                    x1, y1, x2, y2 = map(int, box)

                    # Ensure coordinates are within bounds
                    x1 = max(0, min(x1, width))
                    y1 = max(0, min(y1, height))
                    x2 = max(x1, min(x2, width))
                    y2 = max(y1, min(y2, height))

                    if x2 > x1 and y2 > y1:  # Valid box
                        combined_mask[:, y1:y2, x1:x2] = 1.0
                        valid_detections.append(f"{label}({confidence:.2f})")

                except (ValueError, TypeError):
                    continue

        if debug_mode:
            debug_info.append(f"Combined {len(valid_detections)} detections")

        if valid_detections:
            labels = ", ".join(valid_detections)
            return ("", combined_mask, labels)
        else:
            empty_mask = self._create_empty_mask(height, width)
            return ("No valid detections above threshold", empty_mask, "")

    def _create_empty_mask(self, height: int, width: int) -> torch.Tensor:
        """Create an empty mask tensor with proper memory management."""
        return torch.zeros((1, height, width), dtype=torch.float32, device="cpu")

    def _create_detection_mask(self, x1: int, y1: int, x2: int, y2: int,
                              height: int, width: int) -> torch.Tensor:
        """Create a detection mask tensor with proper bounds checking."""
        mask_tensor = torch.zeros((1, height, width), dtype=torch.float32, device="cpu")
        if x2 > x1 and y2 > y1:  # Valid box
            mask_tensor[:, y1:y2, x1:x2] = 1.0
        return mask_tensor

    def _create_error_response(self, error_msg: str, debug_info: List[str], 
                              height: int = None, width: int = None, debug_mode: bool = False) -> Tuple:
        """Create a standardized error response."""
        if height is None or width is None:
            height, width = 256, 256  # Smaller default to save VRAM

        empty_mask = self._create_empty_mask(height, width)
        debug_output = "\n".join(debug_info) if debug_mode else ""
        return (error_msg, empty_mask, "", debug_output)


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
