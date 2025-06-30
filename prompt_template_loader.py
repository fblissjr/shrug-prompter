# prompt_template_loader.py
import os
import folder_paths

class PromptTemplateLoader:
    """A simple node to load text files from the 'templates' subdirectory."""
    def __init__(self):
        self.script_directory = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(self.script_directory, "templates")
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        self.template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(('.txt', '.md'))]

    @classmethod
    def INPUT_TYPES(cls):
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
        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return (f.read(),)
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            return (f"ERROR: Could not load template {template_name}",)
