# Shrug-Prompter

Clean, memory-efficient VLM nodes for ComfyUI, with state management, looping, keyframe extraction, batching, and built-in templates for Wan2.1, VACE, and beyond.

Initially built and tested with my local (OpenAI API compatible and sorta ollama compatible) vision LLM server, https://github.com/fblissjr/heylookitsanllm, which works with any GGUF or MLX model. Most features will work with any OpenAI-compatible API endpoint, but I've been deviating from that as the performance I needed changed.

Built for Wan2.1, WAN VACE, and FLUX Kontext, but obviously can be extended beyond that. The nodes are generic enough to work with any workflow that needs vision-to-text capabilities and some utility nodes that go along with it.

Handles State Management Looping, Batching, Keyframe Extraction, and many more edge cases that drove me crazy when building this project. If you've ever tried to get VLMs working properly inside ComfyUI loops, you know the pain.

Built with love for Bandoco (and the broader community), where I've learned a ton over the years, and where all the amazing innovation in this space is happening right now.

## What is it?

Shrug-prompter is a set of ComfyUI nodes that connect vision language models (VLMs) to video generation workflows. It lets you analyze keyframes and generate context-aware prompts automatically instead of typing them manually or copying and pasting from other LLMs. There's templates that have been refined with LLMs from datasets and eval datasets that I've found have been correlated with Wan2.1 and VACE prompts (in other words, what I've inferred to be closely aligned with the training dataset). I'm fairly awful at creating workflows, but I've tried to create a few to show how these nodes work together and how the various utility nodes play a role in the overall process.

That all said, the nodes are modular, and you can load your own prompt templates, or edit mine. They're meant as a starter, and are in the `templates` folder as markdown files. Some are few-shot, some are not. The model family and size you use matters. I've found qwen2.5-vl 72B to work best, likely because it's large enough to handle the few-shot examples, and more importantly, it's likely in the same model family as what was used to rewrite the captions used for training Wan2.1. Model family matters here, because of all those little nuances in LLMs and vocabs and tokenization. Few-shot examples tend to work well, but latency can be brutal without prompt caching.

## Why more prompting custom nodes?

I've now spent years obsessively bouncing back and forth between the LLM space the diffusion space, and what's neat is how both sides are now starting to converge more and more. Prompts need to closely align with the training dataset for models that increasingly rely on automated LLM-driven captions (such as those for FLUX Kontext and Wan). Manual captioning doesn't really work, nor is it very fun or scalable trying to fit your language and style and structure to the training dataset, but it does need some human guidance to get wherever it is you want to go. These nodes aim to help with that.

There's tons of custom nodes out there for captioning and prompting for video and image generation, but most tend to come in two flavors: a local/on-device one that runs on the same machine as ComfyUI (and eats up resources, or is kept limited to a small model that doesn't perform very well), or cloud-based ones that hit commercial endpoints. This is squarely in the on-device / local space, but thrives in an environment where you might be driving your daily use with an Apple Silicon Mac or a Linux or Windows machine with enough RAM to run a large capable model.

`shrug-prompter` was born as a more tunable alternative to those, but really was created as a testbed client for an API server I've been working on that unifies Apple's `mlx-lm`, `mlx-vlm`, and `llama.cpp` gguf models, under a single endpoint - called [`heylookitsanllm`](https://github.com/heylookitsanllm/heylookitsanllm). It began as an OpenAI compatible endpoint, and slowly evolved as the features and performance I needed from ComfyUI calling it grew. I added `ollama` API endpoints into it as more of an afterthought, primarily because of how many folks I see running ollama models - which tend to not perform as well due to odd defaults and quirks - but are used because of the ease-of-adoption factor.

Little quality of life feautures, like auto-resizing images via pushing down to the server as multi-part raw messages vs. base64 increased performance by ~33%, and prevented some OOMs in ComfyUI for generations that were already right on the edge of my 4090's limited VRAM. So with that pain came the ability to pass params like `resize_params = ['resize_max', 'resize_width', 'resize_height', 'image_quality', 'preserve_alpha']` - and suddenly I wasn't OpenAI compatible anymore, but more of a superset of sorts.

Due to this, you're unlikely to see as much value with these nodes without also running `heylookitsanllm`. But maybe you will - let me know.

## Quick Start

(this is the first custom node i've invested any real significant time into to get over the finish line - will look into ComfyUI Manager integration soon if there's value here)

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
- Processes frame pairs for smooth transitions
- Uses wan_vace_transition template for best results

## Core Nodes

### VLM Configuration & Processing

**VLM Provider Config** - Set your API endpoint and model
- Point to any OpenAI-compatible endpoint (local or cloud, although you'll find some features just only work with `heylookitsanllm`)
- Auto-detects server capabilities for optimal performance via the `/capabilities` endpoint

**Shrug Prompter** - Main VLM interface with template support
- Smart batch processing - handles single images or batches automatically
- Built-in response cleanup (trim spaces, fix unicode, etc)
- Server-side / pushdown image resizing for ~33% faster processing
- Template support for consistent prompting
- Debug mode shows raw API requests/responses
- Smart JSON parsing - automatically extracts prompts from various response formats

**VLM Image Processor** - All-in-one image prep
- Handles any aspect ratio and size
- Smart memory management
- Optional preprocessing for specific models
- Batch and sequential processing
- Supports 1 image, 2, 4, whatever makes sense for your use case and the model's capabilities

**VLM Image Passthrough** - Zero-copy alternative
- Use this when you don't need preprocessing
- Passes images directly to VLM without copies (meaning no memory overhead, theoretically)

### Video & Frame Management

**Video Frame Pair Extractor** - Get consecutive frame pairs for interpolation
- Works inside ForLoop structures
- Handles edge cases (like odd frame counts)
- Outputs start/end frames for each transition
- Intended for VACE workflows

**Smart Image Range Extractor** - Easier frame extraction
- Should avoid failures on out-of-bounds indices
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

**Auto Memory Manager** - Automatic cleanup -
- Likely will cause more harm than good given how much memory management happens in the background in most good nodes already, but here just in case
- Place after heavy operations
- Multiple aggression levels
- Works with PyTorch and system memory

**Advanced VLM Sampler** - Fine-tune generation
- Extra parameters like top_k, repetition_penalty
- Processing modes for different use cases
- Returns config dict for reuse

## Templates

Pre-built prompt templates in `templates/`:

### For WAN/VACE Workflows:
- `wan_vace_transition.md` - Frame-to-frame transitions (recommended for VACE)
- `wan_vace_frame_description.md` - Single frame analysis
- `wan_vace_batch_transitions.md` - Batch process N frames → N-1 transitions
- `wan_prompt_rewriter_qwen.md` - Image-grounded prompt enhancement

### General Purpose:
- `cinematographer.md` - Updated for WAN-style descriptions
- feel free to add your own or have any LLM modify existing ones to fit your needs

## Tips & Best Practices

### Getting Started
- Start heylookitsanllm first: `heylookllm --api openai` (or use your own)
- Use VLM models with vision support (look for "(Vision)" in dropdown)
- For video workflows: keyframes → frame pairs → prompts → video
- Memory is managed automatically - just connect and go

### Performance Tips
- Use `VLMImagePassthrough` instead of `VLMImageProcessor` when you don't need preprocessing
- Enable `batch_mode=true` in ShrugPrompter for multiple independent images
- Set `resize_mode="max"` with `resize_value=512` for fast processing
- The multipart endpoint is auto-detected and 57ms faster per image

### Multi-Image Handling in ShrugPrompter
**`batch_mode=false` (default):**
- All images sent in ONE message: `[text, image1, image2, image3...]`
- VLM sees all images simultaneously in the same context
- Perfect for: "Compare these frames", "Analyze the transition", "Describe changes between images"
- Use this for WAN VACE frame-to-frame transitions

**`batch_mode=true`:**
- Each image gets its own separate API call
- Returns multiple independent responses
- Good for: Processing many unrelated images efficiently
- Each image is analyzed in isolation

**Example for frame transitions:**
```
StartFrame → ImageBatch → ShrugPrompter (batch_mode=false, template=wan_vace_transition.md)
EndFrame   ↗
```

### Working with Loops
- Always connect FLOW_CONTROL from ForLoopOpen to ForLoopClose
- Use `reset=true` on accumulators if you don't want persistence
- Place AutoMemoryManager after heavy operations in loops
- Loop indices are 0-based, plan accordingly

### Text Cleanup
- Use `response_cleanup="standard"` should work for most cases, but should validate your pre-cleanup and post-cleanup text in the server log
- `"basic"` just trims whitespace
- `"strict"` removes all non-ASCII characters
- Custom cleanup with TextCleanup node for specific needs
- Batch works too

### WAN VACE Workflows
- VACE generates smooth video between keyframes
- Use `wan_vace_transition.md` template for frame pairs
- Each prompt describes the journey from frame A to frame B
- Include all visible elements: subjects, objects, background
- The text encoder expects detailed, grounded descriptions
- For N keyframes, generate N-1 transition prompts

### Debugging
- Enable `debug_mode=true` in ShrugPrompter to see API calls
- Add ShowText nodes to inspect intermediate values
- Check accumulator debug_info output for state tracking
- Timeout: Default 5 minutes per request (configurable in ShrugPrompter node)

## Requirements
- ComfyUI
- LLM / VLM server (`heylookitsanllm` recommended since it's what I'm driving everything from)
  - llama.cpp & mlx + mlx-vlm unified
  - **Note**: RemoteTextEncoder requires heylookitsanllm to have `/v1/embeddings` endpoint implemented
- Vision-capable model (qwen2-vl, gemma3n, mistral small, etc)

Whew, that's a lot. Hope this is helpful for some people, despite it likely being very niche.
