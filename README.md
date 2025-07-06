# 🚀 Shrug-Prompter: Unified VLM Integration for ComfyUI

A comprehensive Vision-Language Model (VLM) integration system for ComfyUI with more intelligent prompt optimization, object detection, template support, and performance optimizations. Optimized for Wan2.1, Flux Kontext, and general purpose. Goes well with my other project, an MLX/llama.cpp server with hot swappable models and ollama api compatibility, (heylookitsanllm)https://github.com/fblissjr/heylookitsanllm]

## What This Does

### 🎯 **Dual-Mode Operation**
1. **Prompt Optimization**: Transform basic prompts into detailed, optimized versions for image generation
2. **Object Detection**: Find and localize objects in images with precise bounding box masks

### 🔧 **Key Features**
- **Dynamic model loading**: Auto-fetch available models from your VLM / LLM server
- **Template system**: Includes dataset-optimized templates for various tasks, including flux kontext, wan2.1, and general purpose
- **Smart caching**: Reduce redundant API calls with built-in response caching
- **Low VRAM and memory footprint**: Optimized memory usage with smart defaults
- **Enhanced debugging**: Optional detailed processing information

## Installation

### 1. **Prerequisites**
```bash
# Make sure you have a VLM server running
heylookitsanllm --api openai --port 8080

# Or any OpenAI-compatible API server
```

### 2. **Install Custom Node**
```bash
# Navigate to your ComfyUI custom nodes directory
cd ComfyUI/custom_nodes/

# Clone or copy the shrug-prompter folder here
# The structure should be: ComfyUI/custom_nodes/shrug-prompter/
```

### 3. **Start ComfyUI**
Restart ComfyUI and the nodes will appear in the **"Shrug Nodes"** category.

## 🎮 Quick Start

### **Basic Workflow**
```
ShrugProviderSelector → ShrugPrompter → ShrugResponseParser
```

### **Configuration**
- **Provider**: "openai"
- **Base URL**: "http://localhost:8080" (your VLM server)
- **API Key**: "not-required-for-local" for local servers
- **Model**: Auto-populated dropdown from your server

## Node Reference

### **ShrugProviderSelector**
Configures connection to your VLM server.

**Settings:**
- `provider`: "openai"
- `base_url`: Your server URL (e.g., "http://localhost:8080")
- `api_key`: API key ("not-required-for-local" for local servers)
- `llm_model`: Model name (dropdown auto-populated from server)

**Output:** Configuration context for other nodes

---

### **ShrugPrompter**
VLM prompter with templates, caching, and enhanced debugging.

**Required Inputs:**
- `context`: From ShrugProviderSelector
- `system_prompt`: System prompt (supports `{{variables}}`)
- `user_prompt`: User prompt (supports `{{variables}}`)
- `max_tokens`, `temperature`, `top_p`: Generation parameters

**Optional Inputs:**
- `images`: Optional images (IMAGE type)
- `mask`: Optional mask (MASK type)
- `template_vars`: JSON string of variables (e.g., `{"style": "cinematic"}`)
- `use_cache`: Enable response caching (default: True)
- `debug_mode`: Show detailed processing info (default: False)

**Output:**
- `context`: Updated context with VLM response

---

### **ShrugResponseParser**
Intelligent response parsing with auto-format detection and debugging.

**Required Inputs:**
- `context`: From prompter

**Optional Inputs:**
- `original_image`: Reference image for correct mask dimensions
- `output_format`: "auto", "text", or "detection" (default: "auto")
- `mask_size`: Default mask size if no reference image (default: 256)
- `confidence_threshold`: Minimum detection confidence (default: 0.5)
- `debug_mode`: Show detailed parsing info (default: False)

**Outputs:**
- `OPTIMIZED_PROMPT`: Text response or detection summary
- `DETECTED_MASK`: Binary mask for detected objects (for inpainting, etc.)
- `DETECTED_LABEL`: Object labels with confidence scores

---

### **ShrugMaskUtilities**
Advanced mask processing operations.

**Operations:**
- `resize`: Change mask dimensions
- `crop`: Extract bounding box region
- `dilate`: Expand mask areas
- `erode`: Contract mask areas
- `combine`: Merge multiple masks

## 🎨 Template System

### **Using Variables**
In your prompts, use `{{variable}}` syntax:

**System Prompt:**
```
You are a {{role}} specializing in {{domain}} imagery.
```

**User Prompt:**
```
Create a {{style}} image of {{subject}} with {{mood}} atmosphere.
```

**Template Variables:**
```json
{
  "role": "professional photographer",
  "domain": "architectural",
  "style": "cinematic",
  "subject": "modern building",
  "mood": "dramatic"
}
```

## 🔍 Use Cases & Examples

### **1. Prompt Optimization**
Transform basic prompts into detailed ones for image generation:

**Template Variables:**
```json
{
  "style": "cinematic",
  "quality": "8K professional",
  "lighting": "golden hour"
}
```

**Input:** "castle"
**Enhanced Output:** "Majestic medieval castle perched on dramatic cliff, cinematic golden hour lighting, 8K professional photography, atmospheric mist..."

### **2. Object Detection**
Find objects and get masks for inpainting/compositing:

**Input:** Image + "Find the person"
**Output:**
- Mask highlighting the person's location
- Label: "person (0.95)"
- Empty text (since it's detection mode)

### **3. Debug Mode**
Enable `debug_mode` on both nodes to see:
- Processing steps and timing
- Template variable substitution
- Cache hit/miss status
- Response format detection
- **Performance metrics from heylookitsanllm**:
  ```
  📊 Performance Metrics:
    ⚡ Processing speed: 24.3 tok/s
    🔄 Model load time: 1.2s
    🧠 Inference time: 6.4s
    📝 Response: 156 tokens
  ✓ Using cached response
  ✓ Templates processed
  ```

## ⚡ Performance Features

### **Memory Optimization**
- Default mask size: 256×256
- Smart image resizing: Max 1024px with quality control
- JPEG compression: Reduces base64 payload by 60-80%
- Automatic GPU memory cleanup

### **Response Caching**
- Built-in response caching with `use_cache` option
- Cache key based on all input parameters
- Automatic cache cleanup when it gets large
- Session-persistent storage

**How Caching Works:**
- 💾 When `use_cache=True` (default), responses are cached based on:
  - Model name, prompts, parameters, image signatures
  - Same inputs = instant cached response (no API call)
- ⚡ **Benefits**: Faster iteration during workflow development
- 🗑️ **Clears**: When ComfyUI restarts or cache gets too large
- 👁️ **Debug**: Enable `debug_mode=True` to see cache hits/misses

*Example debug output:*
```
✓ Using cached response  # Cache hit - instant response
✓ Cached response      # Cache miss - stored for next time
```

### **Dynamic Model Loading**
- JavaScript widget calls ComfyUI's built-in server
- Server fetches models from your VLM API
- Dropdown auto-populates with available models
- Vision-capable models automatically detected

### **Performance Metrics** (when using heylookitsanllm)
In debug mode, see real-time performance data from your local VLM server:
- **Processing speed**: Tokens per second calculation
- **Model loading time**: How long to load/swap models
- **Inference time**: Actual generation duration
- **Token efficiency**: Prompt vs response token usage
- **Memory usage**: VRAM optimization tracking

*Example debug output:*
```
✓ Model loaded in 1.2s
✓ Processing: 24.3 tokens/sec
✓ Response: 156 tokens in 6.4s
✓ VRAM: 8.2GB → 8.9GB (+0.7GB)
```

### **Optional New Features**
Enable new features by setting optional inputs:
- `template_vars`: Add JSON variables for dynamic prompts
- `use_cache`: Enable caching (default: True)
- `debug_mode`: See detailed processing info (default: False)
- `confidence_threshold`: Filter low-confidence detections

## 🔧 Configuration Examples

### **For Local heylookitsanllm Server:**
```
Provider: openai
Base URL: http://localhost:8080
API Key: not-required-for-local
Model: (auto-populated from server)
```

### **For OpenAI API:**
```
Provider: openai
Base URL: https://api.openai.com
API Key: your-actual-openai-key
Model: gpt-3000-vision-preview_2079_whatyearisthis
```

### **Template Variables Examples:**

**Cinematic Photography:**
```json
{
  "style": "cinematic",
  "lighting": "golden hour",
  "composition": "rule of thirds",
  "camera": "85mm lens",
  "quality": "8K professional"
}
```

**Object Detection:**
```json
{
  "target_objects": ["person", "car", "building"],
  "confidence_threshold": 0.7,
  "include_attributes": true
}
```

## 🐛 Troubleshooting

### **Models not loading**
- Check your VLM server is running and accessible
- Verify the base URL is correct
- Check browser console for JavaScript errors
- Try refreshing the node or restarting ComfyUI

### **High memory usage**
- Default settings are already optimized (256×256 masks)
- Enable caching to reduce repeated processing
- Keep images under 1024px (automatic resizing)
- Use debug mode to see memory usage details

### **Response parsing errors**
- Enable `debug_mode` on ShrugResponseParser to see parsing details
- Try `output_format="text"` for debugging
- Verify your model supports vision (for image inputs)
- Test with simple text-only prompts first

### **Template not working**
- Check your JSON syntax in `template_vars`
- Enable `debug_mode` to see template processing
- Use simple variables first: `{"name": "value"}`

## System Architecture

### **How Dynamic Model Loading Works**
1. JavaScript widget calls ComfyUI's built-in web server
2. ComfyUI server calls your VLM server's `/v1/models` endpoint
3. Available models populate the dropdown automatically

### **Data Flow**
```
Images + Text → ShrugPrompter → VLM API → ShrugResponseParser
                     ↓                           ↓
              Template Processing          Smart Format Detection
                     ↓                           ↓
             API Call with Cache         Text OR Detection Masks
```
