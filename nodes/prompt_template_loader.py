# In shrug-prompter/nodes/prompt_template_loader.py
import os
import yaml
import json

class PromptTemplateLoader:
    """
    Loads a prompt template from a file and its subdirectories,
    and extracts its YAML metadata header.
    """
    def __init__(self):
        self.templates_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates")
        self.template_files = []
        if os.path.exists(self.templates_dir):
            # WHY: Use os.walk to recursively search all subdirectories for templates.
            # This makes the node robust to however the user organizes their files.
            for root, _, files in os.walk(self.templates_dir):
                for file in files:
                    if file.endswith(('.txt', '.md')):
                        # Store the relative path from the templates dir
                        relative_path = os.path.relpath(os.path.join(root, file), self.templates_dir)
                        self.template_files.append(relative_path)
        if not self.template_files:
            self.template_files = ["No templates found"]

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"template_name": (cls().template_files,)}}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt_text", "metadata")
    FUNCTION = "load_template"
    CATEGORY = "Shrug Nodes/Logic"

    def load_template(self, template_name):
        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = {"output_type": "single_string"}
            prompt_text = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    front_matter = yaml.safe_load(parts[1])
                    if isinstance(front_matter, dict): metadata.update(front_matter)
                    prompt_text = parts[2].strip()

            return (prompt_text, json.dumps(metadata))
        except Exception as e:
            return (f"ERROR loading {template_name}: {e}", json.dumps({}))
