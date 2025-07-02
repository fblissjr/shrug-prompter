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

        # Determine mask dimensions from the original image to ensure alignment
        if original_image is not None:
            _, height, width, _ = original_image.shape
        else:
            height, width = 512, 512  # Fallback size

        empty_mask = torch.zeros((1, height, width), dtype=torch.float32, device="cpu")

        # Handle error responses
        if not llm_response or "error" in llm_response:
            error_msg = llm_response.get("error", {}).get("message", "Upstream node error")
            print(f"Error in ShrugResponseParser: {error_msg}")
            return (f"ERROR: {error_msg}", empty_mask, "")

        # Extract response text - handle both OpenAI and edge-llm formats
        response_text = ""
        try:
            choices = llm_response.get("choices", [])
            if choices and len(choices) > 0:
                choice = choices[0]

                # Handle different response formats
                if "message" in choice:
                    # Standard OpenAI format
                    response_text = choice["message"].get("content", "")
                elif "delta" in choice:
                    # Streaming format that got collected
                    response_text = choice["delta"].get("content", "")
                elif "text" in choice:
                    # Alternative format
                    response_text = choice["text"]
                else:
                    # Fallback: try to find text content anywhere
                    response_text = str(choice)
            else:
                # No choices found, try other formats
                if "content" in llm_response:
                    response_text = llm_response["content"]
                elif "text" in llm_response:
                    response_text = llm_response["text"]
                else:
                    print(f"WARNING: Unexpected response format: {llm_response}")
                    response_text = str(llm_response)

        except Exception as e:
            print(f"ERROR parsing response: {e}")
            print(f"Response structure: {llm_response}")
            response_text = ""

        if not response_text:
            return ("ERROR: Received empty content from VLM.", empty_mask, "")

        # Clean up response text
        response_text = response_text.strip()

        # Attempt to parse the response as a JSON object for object detection
        try:
            # Try to find JSON in the response (might have extra text around it)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}')

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end+1]
                detection_data = json.loads(json_text)

                if isinstance(detection_data, dict) and "box" in detection_data and "label" in detection_data:
                    box = detection_data.get("box", [])
                    label = detection_data.get("label", "not_found")

                    if label == "not_found" or not box or len(box) != 4:
                        return ("Object not found.", empty_mask, label)

                    try:
                        x1, y1, x2, y2 = map(int, box)

                        # Ensure coordinates are within image bounds
                        x1 = max(0, min(x1, width))
                        y1 = max(0, min(y1, height))
                        x2 = max(x1, min(x2, width))
                        y2 = max(y1, min(y2, height))

                        # Create mask tensor
                        mask_tensor = torch.zeros((1, height, width), dtype=torch.float32, device="cpu")
                        if x2 > x1 and y2 > y1:  # Valid box
                            mask_tensor[:, y1:y2, x1:x2] = 1.0

                        return ("", mask_tensor, label)
                    except (ValueError, TypeError) as e:
                        print(f"ERROR: Invalid box coordinates: {box}, error: {e}")
                        return (f"ERROR: Invalid detection box: {box}", empty_mask, "")

        except (json.JSONDecodeError, TypeError) as e:
            # If not a valid detection JSON, pass it through as a text prompt
            pass

        # Return as optimized prompt
        return (response_text, empty_mask, "")
