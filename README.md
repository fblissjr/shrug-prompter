# Shrug-Prompter

Clean, memory-efficient VLM nodes for ComfyUI, with state management, looping, keyframe extraction, batching, and built-in templates for Wan2.1, VACE, and beyond.

Initially built and tested with my local (OpenAI API compatible and sorta ollama compatible) vision LLM server, https://github.com/fblissjr/heylookitsanllm, which works with any GGUF or MLX model.

Built for Wan2.1, VACE, and FLUX Kontext, but obviously can be extended beyond that.

Handles State Management Looping, Batching, Keyframe Extraction, and many more edge cases that drove me crazy when building this project.

Built with love for Bandoco (and the broader community), where I've learned a ton over the years, and where all the amazing innovation in this space is happening right now.

## What is it?

Shrug-prompter is a set of ComfyUI nodes that connect vision language models (VLMs) to video generation workflows. It lets you analyze keyframes and generate context-aware prompts automatically instead of typing them manually or copying and pasting from other LLMs. There's templates that have been refined with LLMs from datasets and eval datasets that I've found have been correlated with Wan2.1 and VACE prompts (in other words, what I've inferred to be closely aligned with the training dataset).

## Why?

I've spent years in the LLM space, and the diffusion space, while catching up, was trained on using CLIP and simpler captions. Wan2.1 (and HunyuanVideo VACE and FLUX Kontext and the next ones) needs prompts to closely align with the training dataset.

While we don't have access to that, I've put in a ton of effort finding the closest I could to datasets from papers and eval datasets - even going so far as to generate some of the source videos in that bizarrely compressed diffusion sort of way. When you have 7 keyframes and need prompts for each transition, why not let a VLM with a prompt template refined on that write them for you? And if you can do it with your own models and your own compute, even better.

That all said, the nodes are modular, and you can load your own prompt templates, or edit mine. They're all in the templates folder in markdown format - nothing special. Some are few-shot, some are not. The model family and size you use matters. I've found qwen2.5-vl 72B to work best, likely because it's large enough to handle the few-shot examples, and more importantly, it's likely in the same model family as what was used to rewrite the captions used for training Wan2.1. Model family matters here, because of all those little nuances in LLMs and vocabs and tokenization.

## Quick Start

1. Install in ComfyUI custom nodes folder
2. Start your VLM server (heylookitsanllm or any OpenAI-compatible endpoint)
3. Load an example workflow and go

## Example Workflows

### Basic VLM Prompting
`example_workflows/simple_vlm_prompt.json`
- Connect images → VLM → get descriptions
- Shows basic setup with provider config

### Video Frame Interpolation
`example_workflows/video_interpolation_loop.json`
- Extract frame pairs from keyframes
- Generate prompts for each transition
- Works with ForLoop structures

### Batch Processing
`example_workflows/batch_vlm_processing.json`
- Process multiple images in one go
- Automatic memory management
- Accumulate results for downstream use

### WAN/VACE Integration
`example_workflows/wan_vace_vlm.json`
- Replace manual prompts with VLM analysis
- Uses wan_prompt_rewriter template

## Core Nodes

**VLM Provider Config** - Set your API endpoint and model
**Shrug Prompter** - Main VLM interface with template support
**VLM Image Processor** - Prep images for VLM (resize, optimize)
**Video Frame Pair Extractor** - Get start/end frame pairs
**Loop Aware VLM Accumulator** - Collect results across loop iterations

## Templates

Pre-built prompt templates in `templates/`:
- `wan_prompt_rewriter_qwen.md` - For WAN/VACE video generation
- `cinematographer.md` - Cinematic shot descriptions
- Add your own!

## Tips

- Start heylookitsanllm first: `heylookllm --api openai` (or use your own)
- Use VLM models with vision support (look for "(Vision)" in dropdown)
- For video workflows: keyframes → frame pairs → prompts → video
- Memory is managed automatically - just connect and go

## Requirements

- ComfyUI
- VLM server (heylookitsanllm recommended)
- Vision-capable model (qwen2-vl, llava, etc)

That's it. Load a workflow and start generating.
