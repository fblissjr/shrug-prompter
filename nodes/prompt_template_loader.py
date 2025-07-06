# In shrug-prompter/nodes/prompt_template_loader.py
import os
import yaml
import json

class PromptTemplateLoader:
    """
    Loads a prompt template from a file and intelligently separates the
    YAML metadata header from the main prompt content. This allows templates
    to define their own expected output behavior.
    """
    def __init__(self):
        # Standard initialization to locate the templates directory.
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(os.path.dirname(script_dir), "templates")
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        try:
            self.template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(('.txt', '.md'))]
            if not self.template_files: self.template_files = ["No templates found"]
        except Exception as e:
            print(f"Error reading templates directory: {e}")
            self.template_files = ["Error reading templates"]

    @classmethod
    def INPUT_TYPES(cls):
        instance = cls()
        return { "required": { "template_name": (instance.template_files,) } }

    # WHY: The node now has two outputs to decouple the prompt's instructions (prompt_text)
    # from its intended behavior (metadata). This makes the system more modular.
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt_text", "metadata")
    FUNCTION = "load_template"
    CATEGORY = "Shrug Nodes/Logic"

    def load_template(self, template_name):
        """
        Reads a template file, parses its YAML front-matter for metadata,
        and returns the prompt content and metadata as separate outputs.
        """
        if template_name.startswith("No templates") or template_name.startswith("Error"):
            return (template_name, json.dumps({}))

        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # WHY: A default metadata ensures that even templates without a header
            # behave predictably (as a single string output).
            metadata = {"output_type": "single_string", "description": "No metadata found."}
            prompt_text = content

            # WHY: Parsing YAML front-matter allows each template to be self-describing.
            # This is more robust than relying on filenames or user-selected modes.
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        front_matter = yaml.safe_load(parts[1])
                        if isinstance(front_matter, dict):
                            metadata.update(front_matter)
                        prompt_text = parts[2].strip()
                        print(f"Loaded template '{template_name}' with metadata: {metadata}")
                    except yaml.YAMLError:
                        # If YAML is malformed, treat the whole file as a single prompt.
                        prompt_text = content

            return (prompt_text, json.dumps(metadata))

        except Exception as e:
            error_msg = f"ERROR: Could not load template '{template_name}': {e}"
            print(error_msg)
            return (error_msg, json.dumps({}))
