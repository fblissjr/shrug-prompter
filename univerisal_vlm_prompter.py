# universal_vlm_prompter.py
import torch
import numpy as np
from PIL import Image, ImageDraw
import os
import base64
import io

# Safe imports for both providers
try:
    from google import genai
    print("Google GenAI library loaded successfully.")
except ImportError:
    genai = None
    print("Warning: Google GenAI library not found. Gemini provider will not be available.")

try:
    from openai import OpenAI
    print("OpenAI library loaded successfully.")
except ImportError:
    OpenAI = None
    print("Warning: OpenAI library not found. OpenAI provider will not be available.")


# A robust system prompt that instructs the LLM on how to handle all possible inputs.
UNIVERSAL_SYSTEM_PROMPT = """You are an expert prompt engineer for an image-to-video model. Your task is to synthesize user instructions and visual information into a single, detailed, and expressive prompt.

**INPUTS YOU MAY RECEIVE:**
1.  **Primary Image:** The main image to be edited.
2.  **User Instruction:** The user's goal for the edit.
3.  **Mask/Overlay (Optional):** The primary image may have a semi-transparent red overlay highlighting a specific region. If you see this, the user's instruction must **ONLY** apply to the contents within that highlighted area. Describe the edit and explicitly state that everything outside the overlay remains unchanged.
4.  **Secondary Image (Optional):** A second image may be provided for style, character, or object reference.

**YOUR DIRECTIVES:**
- If a **mask** is present, apply the user's instruction *only* to the highlighted region.
- If a **secondary image** is present, use it as a reference for style or content as implied by the instruction.
- Ground all descriptions in the visual details you can see.
- Output ONLY the final, optimized prompt. Do not include conversational text or explanations.
"""

class UniversalVLMPrompter:
    def __init__(self):
        # Initialize clients based on installed libraries and env variables
        self.gemini_initialized = False
        if genai:
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
                self.gemini_initialized = True

        self.openai_initialized = False
        if OpenAI:
            # We will initialize the OpenAI client on-demand in the generate method
            # to allow for UI overrides of the URL and key.
            self.openai_initialized = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (["Gemini", "OpenAI"],),
                "primary_image": ("IMAGE",),
                "user_instruction": ("STRING", {"multiline": True, "default": "Make his shirt red"}),
                "model_name": ("STRING", {"default": "gemini-1.5-pro-latest"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1}),
                "max_tokens": ("INT", {"default": 350, "min": 64, "max": 4096}),
            },
            "optional": {
                "secondary_image": ("IMAGE",),
                "mask": ("MASK",),
                "openai_base_url": ("STRING", {"default": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")}),
                "openai_api_key": ("STRING", {"default": os.environ.get("OPENAI_API_KEY", ""), "multiline": False}),
            }
        }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("optimized_prompt",)
    FUNCTION = "generate"
    CATEGORY = "logic/llm"

    # --- Helper Methods ---
    def _tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        image_np = tensor.squeeze(0).cpu().numpy()
        image_np = (image_np * 255).astype(np.uint8)
        return Image.fromarray(image_np, 'RGB')

    def _pil_to_base64(self, pil_image: Image.Image) -> str:
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def _apply_mask_to_image(self, image_tensor: torch.Tensor, mask_tensor: torch.Tensor) -> Image.Image:
        image_pil = self._tensor_to_pil(image_tensor)
        mask_pil = self._tensor_to_pil(mask_tensor.unsqueeze(0)).convert("L")
        overlay = Image.new('RGBA', image_pil.size, (255, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.bitmap((0, 0), mask_pil, fill=(255, 0, 0, 100)) # 100 for alpha transparency
        return Image.alpha_composite(image_pil.convert('RGBA'), overlay).convert('RGB')

    # --- Main Execution Logic ---
    def generate(self, provider, primary_image, user_instruction, model_name, temperature, max_tokens, secondary_image=None, mask=None, openai_base_url="", openai_api_key=""):
        if provider == "Gemini":
            if not self.gemini_initialized:
                return ("ERROR: Gemini provider selected but not initialized. Check GEMINI_API_KEY.",)
            return self._generate_with_gemini(primary_image, user_instruction, model_name, temperature, secondary_image, mask)
        elif provider == "OpenAI":
            if not self.openai_initialized:
                return ("ERROR: OpenAI provider selected but library not installed.",)
            return self._generate_with_openai(primary_image, user_instruction, model_name, temperature, max_tokens, openai_base_url, openai_api_key, secondary_image, mask)
        else:
            return ("ERROR: Unknown provider selected.",)

    # --- Provider-Specific Generation Methods ---
    def _generate_with_gemini(self, primary_image, user_instruction, model_name, temperature, secondary_image=None, mask=None):
        try:
            model = genai.GenerativeModel(model_name)

            prompt_parts = [UNIVERSAL_SYSTEM_PROMPT, f"\n\nUser Instruction: '{user_instruction}'\n\nOptimized Prompt:"]

            # Prepare primary image (with mask if provided)
            image_to_send = self._apply_mask_to_image(primary_image, mask) if mask is not None else self._tensor_to_pil(primary_image)
            prompt_parts.append(image_to_send)

            # Prepare secondary image if it exists
            if secondary_image is not None:
                prompt_parts.append(self._tensor_to_pil(secondary_image))

            response = model.generate_content(prompt_parts, generation_config={"temperature": temperature})
            optimized_prompt = response.text.strip()
            print(f"Gemini Generated Prompt: {optimized_prompt}")
            return (optimized_prompt,)
        except Exception as e:
            return (f"ERROR during Gemini generation: {e}",)

    def _generate_with_openai(self, primary_image, user_instruction, model_name, temperature, max_tokens, base_url, api_key, secondary_image=None, mask=None):
        try:
            client = OpenAI(base_url=base_url, api_key=api_key)

            content_list = [{"type": "text", "text": f"User Instruction: '{user_instruction}'"}]

            # Prepare primary image (with mask if provided)
            image_to_send = self._apply_mask_to_image(primary_image, mask) if mask is not None else self._tensor_to_pil(primary_image)
            primary_base64 = self._pil_to_base64(image_to_send)
            content_list.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{primary_base64}"}})

            # Prepare secondary image
            if secondary_image is not None:
                secondary_base64 = self._pil_to_base64(self._tensor_to_pil(secondary_image))
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{secondary_base64}"}})

            messages = [
                {"role": "system", "content": UNIVERSAL_SYSTEM_PROMPT},
                {"role": "user", "content": content_list}
            ]

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            optimized_prompt = response.choices[0].message.content.strip()
            print(f"OpenAI Generated Prompt: {optimized_prompt}")
            return (optimized_prompt,)
        except Exception as e:
            return (f"ERROR during OpenAI generation: {e}",)
