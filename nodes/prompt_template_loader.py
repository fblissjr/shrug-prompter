# shrug-prompter/nodes/prompt_template_loader.py
import os
import yaml
import json

class PromptTemplateLoader:
    """
    Loads a prompt template and its YAML metadata header.
    """
    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(os.path.dirname(script_dir), "templates")
        if not os.path.exists(self.templates_dir): os.makedirs(self.templates_dir)
        try:
            self.template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(('.txt', '.md'))]
            if not self.template_files: self.template_files = ["No templates found"]
        except Exception as e:
            self.template_files = ["Error reading templates"]
            print(f"Error reading templates directory: {e}")

    @classmethod
    def INPUT_TYPES(cls):
        return { "required": { "template_name": (cls().template_files,) } }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt_text", "metadata")
    FUNCTION = "load_template"
    CATEGORY = "Shrug Nodes/Logic"

    def load_template(self, template_name):
        """Reads a template, parses YAML front-matter, and returns content and metadata."""
        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {"output_type": "single_string"} # Default behavior
            prompt_text = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = yaml.safe_load(parts[1])
                    if isinstance(front_matter, dict):
                        metadata.update(front_matter)
                    prompt_text = parts[2].strip()

            return (prompt_text, json.dumps(metadata))
        except Exception as e:
            return (f"ERROR: Could not load template '{template_name}': {e}", json.dumps({}))
