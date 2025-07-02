# In shrug-prompter/nodes/prompt_template_loader.py
import os

class PromptTemplateLoader:
    """
    A utility node that loads system prompt "personas" from text files in the
    'templates' subdirectory, allowing for easy switching of VLM instructions.
    """
    def __init__(self):
        # Get the directory containing this file
        script_directory = os.path.dirname(os.path.realpath(__file__))

        # Go up one level from nodes/ to get to the main directory, then into templates/
        self.templates_dir = os.path.join(os.path.dirname(script_directory), "templates")

        # Create templates directory if it doesn't exist
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            # Create a default template
            default_template = """You are a helpful assistant specialized in analyzing and describing images.

When given an image, provide a detailed description focusing on:
1. Main subjects and their appearance
2. Setting and environment
3. Colors, lighting, and mood
4. Any notable details or interesting elements

Be descriptive but concise."""

            default_path = os.path.join(self.templates_dir, "default_assistant.md")
            with open(default_path, 'w', encoding='utf-8') as f:
                f.write(default_template)

        # Get list of template files
        try:
            all_files = os.listdir(self.templates_dir)
            self.template_files = [f for f in all_files if f.endswith(('.txt', '.md'))]

            # Ensure we have at least one template
            if not self.template_files:
                self.template_files = ["No templates found - check templates directory"]
        except Exception as e:
            print(f"Error reading templates directory: {e}")
            self.template_files = ["Error reading templates"]

    @classmethod
    def INPUT_TYPES(cls):
        instance = cls()
        return {
            "required": {
                "template_name": (instance.template_files, {"default": instance.template_files[0] if instance.template_files else "default"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_text",)
    FUNCTION = "load_template"
    CATEGORY = "Shrug Nodes/Logic"

    def load_template(self, template_name):
        """Reads the content of the selected file and returns it as a string."""
        if template_name.startswith("No templates") or template_name.startswith("Error"):
            return (template_name,)

        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"Loaded template: {template_name} ({len(content)} characters)")
                return (content,)
        except Exception as e:
            error_msg = f"ERROR: Could not load template '{template_name}': {e}"
            print(error_msg)
            return (error_msg,)
