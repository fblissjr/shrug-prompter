# nodes/prompter.py
from ..utils import tensors_to_base64_list, run_async
from ..shrug_router import send_request

class ShrugPrompter:
    """
    The core processing node. It consumes a `context` dictionary, assembles
    the prompt and image data into a request payload, and dispatches it to the
    appropriate VLM provider via the shrug_router.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 256, "min": 1, "max": 4096}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0}),
            },
            "optional": {
                "images": ("IMAGE",),
                "mask": ("MASK",)
            },
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("context",)
    FUNCTION = "execute_prompt"
    CATEGORY = "Shrug Nodes/Logic"

    def execute_prompt(self, context, system_prompt, user_prompt, max_tokens, temperature, top_p, images=None, mask=None):
        """Execute the VLM prompt request."""

        # Extract provider configuration
        provider_config = context.get("provider_config")
        if not provider_config:
            raise ValueError("A `provider_config` from a ShrugProviderSelector is required.")

        print(f"Processing prompt with model: {provider_config.get('llm_model', 'unknown')}")

        # Convert images to base64 if provided
        image_b64_list = []
        if images is not None:
            try:
                image_b64_list = tensors_to_base64_list(images)
                print(f"Converted {len(image_b64_list)} image(s) to base64")
            except Exception as e:
                print(f"ERROR converting images to base64: {e}")
                image_b64_list = []

        # Convert mask to base64 if provided
        mask_b64 = None
        if mask is not None:
            try:
                mask_b64_list = tensors_to_base64_list(mask)
                mask_b64 = mask_b64_list[0] if mask_b64_list else None
                if mask_b64:
                    print("Converted mask to base64")
            except Exception as e:
                print(f"ERROR converting mask to base64: {e}")

        # Build user content (text + images)
        user_content = [{"type": "text", "text": user_prompt}]

        # Add images to the user content
        for img_b64 in image_b64_list:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })

        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        # Prepare request parameters
        request_kwargs = {
            "provider": provider_config["provider"],
            "base_url": provider_config["base_url"],
            "api_key": provider_config["api_key"],
            "llm_model": provider_config["llm_model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }

        # Add mask if provided (custom extension for some servers)
        if mask_b64:
            request_kwargs["mask"] = mask_b64

        print(f"Sending request to {provider_config['provider']} at {provider_config['base_url']}")

        # Execute the request
        try:
            response_data = run_async(send_request(**request_kwargs))

            # Store response in context
            context["llm_response"] = response_data

            # Log success
            if "error" not in response_data:
                choices = response_data.get("choices", [])
                if choices:
                    content_preview = str(choices[0]).get("message", {}).get("content", "")[:100]
                    print(f"SUCCESS: Received response: {content_preview}...")
                else:
                    print("SUCCESS: Received response (no choices)")
            else:
                print(f"ERROR in response: {response_data['error']}")

        except Exception as e:
            print(f"ERROR executing prompt: {e}")
            context["llm_response"] = {"error": {"message": str(e)}}

        return (context,)
