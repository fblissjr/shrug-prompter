# Shrug-Prompter

Clean, memory-efficient VLM nodes for ComfyUI, with state management, looping, keyframe extraction, batching, and built-in templates for Wan2.1, VACE, and beyond.

Initially built and tested with my local (OpenAI API compatible and sorta ollama compatible) vision LLM server, https://github.com/fblissjr/heylookitsanllm, which works with any GGUF or MLX model. But it'll work with any OpenAI-compatible API endpoint - local or cloud.

Built for Wan2.1, WAN VACE, and FLUX Kontext, but obviously can be extended beyond that. The nodes are generic enough to work with any workflow that needs vision-to-text capabilities.

Handles State Management Looping, Batching, Keyframe Extraction, and many more edge cases that drove me crazy when building this project. If you've ever tried to get VLMs working properly inside ComfyUI loops, you know the pain.

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

### VLM Configuration & Processing

**VLM Provider Config** - Set your API endpoint and model
- Point to any OpenAI-compatible endpoint (local or cloud)
- Auto-detects server capabilities for optimal performance
- Works with heylookllm, ollama, or cloud providers

**Shrug Prompter** - Main VLM interface with template support
- Smart batch processing - handles single images or batches automatically
- Built-in response cleanup (trim spaces, fix unicode, etc)
- Server-side image resizing for 57ms faster processing
- Template support for consistent prompting
- Debug mode shows raw API requests/responses
- Smart JSON parsing - automatically extracts prompts from various response formats

**VLM Image Processor** - All-in-one image prep (replaces 5 old nodes)
- Handles any aspect ratio and size
- Smart memory management
- Optional preprocessing for specific models

**VLM Image Passthrough** - Zero-copy alternative
- Use this when you don't need preprocessing
- Passes images directly to VLM without copies
- Massive memory savings for large batches

### Video & Frame Management

**Video Frame Pair Extractor** - Get consecutive frame pairs for interpolation
- Works inside ForLoop structures
- Handles edge cases (like odd frame counts)
- Outputs start/end frames for each transition

**Smart Image Range Extractor** - Robust frame extraction
- Never fails on out-of-bounds indices
- Handles single images, empty batches
- Works with dynamic loop indices

**Video Segment Assembler** - Reassemble video segments
- Multiple streaming modes
- Handles overlapping segments
- Preserves temporal coherence

### Loop & Accumulation

**Loop Aware VLM Accumulator** - Collect results across loop iterations
- Works properly inside ForLoop structures
- Handles both single and batch responses
- Optional reset to clear previous runs
- Extracts cleaned responses automatically

**Loop Aware Response Iterator** - Access accumulated results by index
- Syncs with ForLoop indices
- Handles empty results gracefully
- Backward compatible with old workflows

**Loop Safe Accumulator** - Original accumulator for simple cases
- Use when you need basic accumulation
- No persistence between runs

### Text Processing

**Text Cleanup** - Clean LLM responses
- Remove leading/trailing spaces
- Fix unicode characters (smart quotes → regular quotes)
- Remove newlines, collapse whitespace
- Strip to ASCII-only if needed
- Custom replacements via simple patterns

**Text List Cleanup** - Same but for lists of text
- Process batch responses
- Join with custom separators (like "|" for WAN)
- Maintain order and indexing

**Text List Indexer** - Extract single item from list
- Essential for connecting VLM lists to nodes expecting strings
- Handles out-of-bounds gracefully

### Utilities

**Prompt Template Loader** - Load markdown templates
- Searches templates/ directory recursively
- Supports YAML frontmatter for metadata
- Templates can be few-shot or zero-shot

**Auto Memory Manager** - Automatic cleanup
- Place after heavy operations
- Multiple aggression levels
- Works with PyTorch and system memory

**Advanced VLM Sampler** - Fine-tune generation
- Extra parameters like top_k, repetition_penalty
- Processing modes for different use cases
- Returns config dict for reuse

## Templates

Pre-built prompt templates in `templates/`:
- `wan_prompt_rewriter_qwen.md` - For WAN/VACE video generation
- `cinematographer.md` - Cinematic shot descriptions
- Add your own!

## Tips & Best Practices

### Getting Started
- Start heylookitsanllm first: `heylookllm --api openai` (or use your own)
- Use VLM models with vision support (look for "(Vision)" in dropdown)
- For video workflows: keyframes → frame pairs → prompts → video
- Memory is managed automatically - just connect and go

### Performance Tips
- Use `VLMImagePassthrough` instead of `VLMImageProcessor` when you don't need preprocessing
- Enable `batch_mode=true` in ShrugPrompter for multiple images
- Set `resize_mode="max"` with `resize_value=512` for fast processing
- The multipart endpoint is auto-detected and 57ms faster per image

### Working with Loops
- Always connect FLOW_CONTROL from ForLoopOpen to ForLoopClose
- Use `reset=true` on accumulators if you don't want persistence
- Place AutoMemoryManager after heavy operations in loops
- Loop indices are 0-based, plan accordingly

### Text Cleanup
- Use `response_cleanup="standard"` for WAN/VACE compatibility
- `"basic"` just trims whitespace
- `"strict"` removes all non-ASCII characters
- Custom cleanup with TextCleanup node for specific needs

### Debugging
- Enable `debug_mode=true` in ShrugPrompter to see API calls
- Add ShowText nodes to inspect intermediate values
- Check accumulator debug_info output for state tracking
- Timeout: Default 5 minutes per request (configurable in ShrugPrompter node)

## Requirements

- ComfyUI
- VLM server (heylookitsanllm recommended)
- Vision-capable model (qwen2-vl, llava, etc)

That's it. Load a workflow and start generating.
