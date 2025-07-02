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
        # ... (INPUT_TYPES remain the same)
        return {
            "required": {
                "context": ("*",),
                "system_prompt": ("STRING", {"multiline": True}),
                "user_prompt": ("STRING", {"multiline": True}),
                "max_tokens": ("INT", {"default": 256}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0}),
            },
            "optional": {"images": ("IMAGE",), "mask": ("MASK",)},
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("context",)
    FUNCTION = "execute_prompt"
    CATEGORY = "Shrug Nodes/Logic"

    def execute_prompt(self, context, system_prompt, user_prompt, max_tokens, temperature, top_p, images=None, mask=None):
        provider_config = context.get("provider_config")
        if not provider_config:
            raise ValueError("A `provider_config` from a ShrugProviderSelector is required.")

        image_b64_list = tensors_to_base64_list(images) if images is not None else []
        mask_b64 = tensors_to_base64_list(mask) if mask is not None else None

        user_content = [{"type": "text", "text": user_prompt}]
        for img_b64 in image_b64_list:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]

        request_kwargs = {**provider_config, "messages": messages, "mask": mask_b64, "max_tokens": max_tokens, "temperature": temperature, "top_p": top_p}

        response_data = run_async(send_request(**request_kwargs))
        context["llm_response"] = response_data

        return (context,)
