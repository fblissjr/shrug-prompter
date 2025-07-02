# Shrug Prompter: A Modular VLM Prompting Toolkit for ComfyUI

A suite of custom nodes for ComfyUI designed to interface with multimodal Vision Language Models (VLMs).

This toolkit provides a structured, modular workflow for generating text prompts or object-detection masks from images. It uses a provider-agnostic architecture, starting with support for any OpenAI-compatible API and designed for straightforward expansion - though it has been optimized for MLX and llama.cpp local LLMs for now.

---

### Features

*   **Modular Workflow:** Uses a chain of single-responsibility nodes (`Provider Selector` -> `VLM Prompter` -> `Response Parser`) for a clear and flexible data pipeline.
*   **Configurable Backend:** Supports any OpenAI-compatible API, allowing for use with both cloud services and local servers.
*   **Dynamic Model Loading:** The `llm_model` dropdown is populated automatically by querying the configured provider's `/v1/models` endpoint.
*   **Conditional Output:** Parses the VLM response to conditionally output either a refined text prompt or a `MASK` and `LABEL` for object detection tasks.
*   **Template-Driven System Prompts:** Use the `Prompt Template Loader` to manage and switch between different system prompt "personas" stored in simple text files.

### 1. Installation

1.  **Clone the repository:**
    Navigate to your `ComfyUI/custom_nodes/` directory.
    ```bash
    git clone https://github.com/your-repo/shrug-prompter
    ```

2.  **Install dependencies:**
    `cd` into the new directory and install the required libraries.
    ```bash
    cd shrug-prompter
    pip install -r requirements.txt
    ```

3.  **Restart ComfyUI:**
    A full restart of the ComfyUI server is required.

### 2. Configuration & Usage

The core workflow consists of chaining three nodes together.

1.  **Provider Selector (Shrug):**
    *   Select your `provider` (e.g., "openai").
    *   Set the `base_url` for the API endpoint.
    *   Provide your `api_key`. The `llm_model` dropdown will populate based on these settings.
    *   **Note:** For convenience, you can set `OPENAI_API_KEY` and `OPENAI_BASE_URL` as environment variables, which the node will use as default values.

2.  **VLM Prompter (Shrug):**
    *   Connect the `context` output from the Provider Selector.
    *   Provide the `system_prompt` and `user_prompt`.
    *   Optionally, connect `IMAGE` and `MASK` inputs.

3.  **Response Parser (Shrug):**
    *   Connect the `context` output from the VLM Prompter.
    *   The node will output either an `OPTIMIZED_PROMPT` string or a `DETECTED_MASK` and `DETECTED_LABEL`, depending on the VLM's response.
