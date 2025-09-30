# shrug-prompter/nodes/prompt_batch_loader.py
import os
import folder_paths

MAX_OUTPUTS = 16

class ShrugPromptBatchFromFile:
    """
    Loads a list of prompts from a text file (one prompt per line) specified by a
    string path and outputs a specific batch of them to 16 individual outputs,
    controlled by an index.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # --- THE FIX IS HERE ---
                # Changed from a dropdown to a standard STRING input.
                "filename": ("STRING", {"default": "prompts.txt", "multiline": False}),
                # --- END OF FIX ---
                "index": ("INT", {"default": 0, "min": 0, "forceInput": True}),
                "batch_size": ("INT", {"default": MAX_OUTPUTS, "min": 1, "max": MAX_OUTPUTS, "step": 1}),
            }
        }

    RETURN_TYPES = tuple(["STRING"] * MAX_OUTPUTS)
    RETURN_NAMES = tuple([f"prompt_{i+1}" for i in range(MAX_OUTPUTS)])
    FUNCTION = "load_batch_from_file"
    CATEGORY = "Shrug Nodes/Logic"

    def load_batch_from_file(self, filename: str, index: int, batch_size: int):
        """
        Loads prompts from a file, splits by newline, and outputs a specific batch.
        """
        # We assume the filename is relative to the ComfyUI 'input' directory.
        # You can also provide an absolute path.
        if not os.path.isabs(filename):
            file_path = folder_paths.get_full_path("input", filename.strip())
        else:
            file_path = filename.strip()

        try:
            if not os.path.exists(file_path):
                 raise FileNotFoundError(f"Prompt file not found at '{file_path}'. Make sure it's in your ComfyUI input directory or the path is absolute.")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.strip().split('\n')
            valid_prompts = [line.strip() for line in lines if line.strip()]

        except Exception as e:
            print(f"ERROR [ShrugPromptBatchFromFile]: {e}")
            return ("",) * MAX_OUTPUTS # Return empty on error

        if not valid_prompts:
            return ("",) * MAX_OUTPUTS

        start_index = index * batch_size
        prompt_slice = valid_prompts[start_index : start_index + batch_size]

        outputs = list(prompt_slice)
        while len(outputs) < MAX_OUTPUTS:
            outputs.append("") # Pad with empty strings

        return tuple(outputs)
