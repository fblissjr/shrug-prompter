# nodes/audio_utils.py
import os
from pydub import AudioSegment

class LoadAudio:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = "input" # ComfyUI's input directory
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {"required": {"audio": (sorted(files), )}}

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "load_audio"
    CATEGORY = "Shrug Nodes/Audio"

    def load_audio(self, audio: str):
        audio_path = os.path.join("input", audio)
        # We will pass the path, not the data itself
        return (audio_path,)
