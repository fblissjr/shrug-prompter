# prompt_template_loader.py
# Purpose: A utility node that loads system prompt "personas" from text files.
# This allows users to create and switch between different sets of instructions
# for the VLM without needing to edit any Python code.

import os
import folder_paths

class PromptTemplateLoader:
    def __init__(self):
        # Locates the 'templates' subdirectory within this custom node's folder.
        self.script_directory = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(self.script_directory, "templates")

        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)

        # Finds all .txt and .md files to populate the dropdown menu.
        self.template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(('.txt', '.md'))]

    @classmethod
    def INPUT_TYPES(cls):
        # Defines the node's inputs in the ComfyUI interface.
        instance = cls()
        return {
            "required": {
                "template_name": (instance.template_files,),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_text",)
    FUNCTION = "load_template"
    CATEGORY = "Shrug Nodes/Logic"

    def load_template(self, template_name):
        # Reads the content of the selected file and returns it as a string output.
        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return (f.read(),)
        except Exception as e:
            print(f"ERROR: Could not load template {template_name}: {e}")
            return (f"ERROR: Could not load template {template_name}",)
