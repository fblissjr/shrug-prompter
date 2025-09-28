# nodes/asr_prompter.py
import base64
import requests

class ShrugASRNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("VLM_CONTEXT",),
                "audio_path": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("transcribed_text",)
    FUNCTION = "transcribe"
    CATEGORY = "Shrug Nodes/Audio"

    def transcribe(self, context: dict, audio_path: str):
        provider_config = context.get("provider_config", {})
        base_url = provider_config.get("base_url", "").rstrip("/")
        model_id = provider_config.get("llm_model") # The ASR model ID

        if not base_url or not model_id:
            raise ValueError("Provider config with base_url and model is required.")

        url = f"{base_url}/v1/audio/transcriptions"

        with open(audio_path, 'rb') as f:
            files = {'file': (os.path.basename(audio_path), f)}
            data = {'model': model_id}

            response = requests.post(url, files=files, data=data)
            response.raise_for_status() # Raise an exception for bad status codes

            transcribed_text = response.json().get("text", "")

        return (transcribed_text,)
