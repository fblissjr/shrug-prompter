# shrug-prompter - universal vlm / multimodal prompter nodes for comfyui

generates text outputs from images by leveraging multimodal vision language models VLMs.

provider-agnostic, allowing you to switch between OpenAI-compatible API and local LLMs or the Google Gemini API

## Features

- **Multimodal Input:** Can process up to two images (primary and secondary) and a mask simultaneously.
- **Mask Support:** Automatically visualizes a mask as a red overlay for the VLM, enabling highly targeted edits.
- **Configurable OpenAI Endpoint:** Easily override the base URL and API key to connect to local models.
- **Sequential Editing Ready:** Designed to be used in loops where the output of one step becomes the input for the next.

Of course. This is the perfect evolution of the project. Creating a single, powerful, and provider-agnostic node is the ultimate goal for a flexible and future-proof workflow.

Here is the complete, final code base for your custom node library, which I'll call `shrug-prompter`. It features a single, unified node called `Universal VLM Prompter` that abstracts the model provider and supports all the advanced features we've discussed.

---

### **Project Structure**

Your `ComfyUI/custom_nodes/shrug-prompter/` directory should contain the following files:

```
shrug-prompter/
├── __init__.py
├── universal_vlm_prompter.py
├── README.md
└── requirements.txt
```

---

### **File 1: `requirements.txt`**

This file lists the necessary Python libraries.

```txt
google-generativeai
openai
```

### **File 2: `README.md`**

Good documentation is essential. This file explains how to install and configure the node.

```markdown
# Shrug Prompter - Universal VLM Prompter for ComfyUI

This custom node provides a single, powerful interface to generate descriptive prompts for image-to-video models by leveraging multimodal Vision Language Models (VLMs).

It is provider-agnostic, allowing you to switch between the Google Gemini API and any OpenAI-compatible API (including local servers like `mlx-vlm`).

## Features

- **Provider Agnostic:** Switch between "Gemini" and "OpenAI" providers directly in the node.
- **Multimodal Input:** Can process up to two images (primary and secondary) and a mask simultaneously.
- **Mask Support:** Automatically visualizes a mask as a red overlay for the VLM, enabling highly targeted edits.
- **Configurable OpenAI Endpoint:** Easily override the base URL and API key to connect to local models.
- **Sequential Editing Ready:** Designed to be used in loops where the output of one step becomes the input for the next.

## Installation

1.  **Clone the Repository:**
    Navigate to your `ComfyUI/custom_nodes/` directory and clone this repository.
    ```bash
    git clone <your-repo-url-here> shrug-prompter
    ```

2.  **Install Dependencies:**
    Navigate into the new directory and install the required libraries.
    ```bash
    cd shrug-prompter
    pip install -r requirements.txt
    ```

3.  **Restart ComfyUI:** Restart your ComfyUI instance completely.

### For OpenAI or Local Servers (`mlx-vlm`)

You can use the UI fields to set the URL and key, but for a persistent setup, set these environment variables:

```bash
# For the official OpenAI API
export OPENAI_API_KEY="your_openai_api_key"

# For a local mlx-vlm server (example)
export OPENAI_BASE_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="no-key-required"
```
**Note:** You can always override these environment variables by filling in the `openai_base_url` and `openai_api_key` fields directly on the node in ComfyUI.

### For Google Gemini

Set the following environment variable in your system or terminal:
```bash
export GEMINI_API_KEY="your_google_ai_studio_api_key"
```
