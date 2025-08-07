# CLAUDE.md - Shrug Prompter

This file provides guidance to Claude Code when working with the shrug-prompter ComfyUI custom nodes.

## Code and Writing Style Guidelines

- **No emojis** in code, display names, or documentation
- Keep all naming and display text professional
- Avoid "Enhanced", "Advanced", "Ultimate" type prefixes - use descriptive names instead
- Clean, simple node names that describe what they do

## Project Overview

Shrug-prompter is a collection of ComfyUI custom nodes for advanced VLM (Vision Language Model) processing, particularly focused on video generation workflows with frame interpolation and batch processing.

## Recent Major Changes (2025)

### Performance Optimizations (Latest)
- **Zero-copy image operations** - VLMImagePassthrough avoids creating copies
- **Server-side resizing** - Advanced resize options in VLM nodes:
  - `resize_mode`: "max" (maintain aspect), "width", "height", "exact" (both dimensions), "none"
  - `resize_value`: Size in pixels for max/width/height modes
  - `resize_width/height`: Specific dimensions for exact mode
  - `image_quality`: JPEG quality 1-100 (default: 85)
  - `preserve_alpha`: Keep transparency, output PNG
- **Automatic multipart detection** - 57ms faster per image when available
- **Raw image bytes** - 33% less bandwidth with multipart endpoint
- **Capability detection** - Auto-detects and uses server optimizations

### Text Processing & Cleanup (Latest)
- **Built-in response cleanup** in ShrugPrompter:
  - `response_cleanup`: "none", "basic", "standard", "strict"
  - Handles leading spaces, unicode normalization, newline removal
  - "standard" recommended for WAN/VACE workflows
- **Smart JSON parsing** - Automatically extracts prompts from various response formats
- **TextCleanup nodes** - Flexible text processing with custom operations
- **Debug mode enhancements** - Shows raw API requests/responses with actual characters

### Batch Processing Refactor
- **ShrugPrompter with `batch_mode=true`** now makes separate API calls for each image instead of bundling them with conversation boundaries
- This prevents OOM errors but changes how image batches flow through workflows
- Removed the problematic `___CONVERSATION_BOUNDARY___` approach

### Node Consolidation (36 → 17 nodes)
- Consolidated from 36 confusing nodes to 17 essential nodes
- Added automatic memory management to all nodes
- Backward compatibility for existing workflows
- Clear naming conventions (VLM*, Video*, etc.)

### New Architecture Features
- **Automatic memory management** - No manual cleanup needed
- **Zero-copy operations** - Views instead of copies where possible
- **Loop-aware accumulation** - Works properly inside ForLoop structures
- **Robust error handling** - Nodes don't fail on edge cases
- **Accumulator cleanup** - Prevents memory buildup across runs
- **Smart response extraction** - Uses cleaned responses when available

## Key Concepts

### Video Interpolation Workflows
These workflows process keyframes (e.g., 4 images) to generate smooth video transitions:
1. Extract pairs of frames (start→end) using ImagePairIterator
2. Use VLM to analyze what should happen between frames
3. Generate video segments for each pair
4. Reassemble into final video using ImageBatchReassembler

### Processing Modes
- **conversation** - Multiple images in one request (e.g., "compare these images")
- **sequential** - Process images one by one (batch mode)
- **batch_mode=true** - Makes separate API calls for each image automatically

### Memory Management (Updated 2025)
- **Use VLMImagePassthrough instead of VLMImageProcessor** - Zero copies!
- **Server-side resizing** - Use resize parameters in VLMPrompter nodes:
  - `resize_mode="max"` with `resize_value=512` for typical use
  - Smaller values (256-384) for faster processing
  - Larger values (768-1024) for more detail
- **Automatic multipart** - Raw image bytes instead of base64 when available
- **Avoid client-side resizing** - Let heylookllm handle it efficiently

### Memory Leak Prevention (Critical Update)
- **ShrugPrompter cache now disabled by default** - Set `use_cache=False`
- **Reduced cache sizes** - Max 10 entries (was 50)
- **Aggressive cleanup** - Accumulators limited to 2-3 instances
- **New GlobalMemoryCleanup node** - Clear all caches/accumulators
- **Per-node cleanup options** - `clear_cache`, `clear_all`, `reset` parameters

## Critical: ForLoop Structure

When using ForLoop nodes from execution-inversion-demo-comfyui:
- **ForLoopOpen** has 3 outputs: INDEX (0), TOTAL (1), and **FLOW_CONTROL (2)**
- **ForLoopClose** requires the FLOW_CONTROL connection on its input
- Without this connection, the loop won't execute properly!

Example structure:
```
ForLoopOpen → [Your Processing Nodes] → ForLoopClose
      ↓                                        ↑
      └──────── FLOW_CONTROL (output 2) ──────┘
```

## Common Workflow Patterns

### Simple Batch VLM Processing (Updated)
```
LoadImages → VLMImagePassthrough → ShrugPrompter (batch_mode=true, resize_mode="max", resize_value=512) → VLMResultCollector
```
Note: Use VLMImagePassthrough for zero-copy operation. Set resize parameters for server-side resizing.

### Common Resize Configurations
```python
# Quick analysis (smaller, faster)
resize_mode="max", resize_value=384, image_quality=70

# Detailed analysis (larger, better quality)
resize_mode="max", resize_value=768, image_quality=90

# Thumbnail preview
resize_mode="max", resize_value=256, image_quality=60

# Exact dimensions (may distort)
resize_mode="exact", resize_width=512, resize_height=512

# Preserve transparency
preserve_alpha=True, image_quality=95
```

### Video Interpolation with Frame Pairs
```
LoadImages → ForLoopOpen → ImagePairIterator → VLM Analysis → Video Gen → ForLoopClose
                   ↓                                                              ↑
                   └────────────── FLOW_CONTROL ─────────────────────────────────┘
```

### VLM-Guided Video Generation
```
Keyframes → Extract Pairs → VLM Analysis → Prompted Video Gen → Reassemble
```

## Node Categories (21 Essential Nodes)

### Core VLM Nodes (6)
- **VLMProviderConfig** - Configure API endpoints and models
  - Auto-detects server capabilities (multipart, resize support)
  - Works with any OpenAI-compatible endpoint
- **ShrugPrompter** - Enhanced VLM prompter with template support
  - Built-in response cleanup (trim, unicode, newlines)
  - Smart JSON parsing for various response formats
  - Debug mode with detailed API logging
  - Batch mode for efficient multi-image processing
  - Cache disabled by default (`use_cache=False`)
  - Configurable cache size and cleanup
- **VLMPrompter** - Fast, memory-efficient alternative
  - Lightweight option for simple use cases
- **VLMImageProcessor** - All-in-one image processing (replaces 5 nodes)
  - Smart preprocessing based on model requirements
- **VLMResultCollector** - Efficient result collection
  - Limited to 2 collectors by default
  - `clear_all` and `max_collectors` options
- **VLMResultIterator** - Access results by index
  - Works with ForLoop indices

### Video Workflow Nodes (4)
- **VideoFramePairExtractor** - Extract start/end frames for interpolation
  - Handles consecutive pairs (0→1, 1→2, 2→3)
  - Works with dynamic loop indices
- **VideoSegmentAssembler** - Assemble segments with streaming modes
  - Multiple assembly strategies
  - Handles overlapping segments
- **SmartImageRangeExtractor** - Robust range extraction
  - Never fails on out-of-bounds
  - Handles edge cases gracefully
- **AutoMemoryManager** - Automatic memory cleanup
  - Multiple aggression levels
  - Place after heavy operations

### Loop Compatibility (5)
- **LoopAwareVLMAccumulator** - Works inside ForLoop structures
  - Now with automatic cleanup of old accumulators (max 3)
  - Uses cleaned_responses when available
  - Reset option to clear between runs
  - `clear_all` option to clear ALL accumulators
- **LoopAwareResponseIterator** - Loop-compatible iteration
  - Syncs with ForLoop indices
- **EnhancedShrugPrompter** - Full backward compatibility
- **RobustImageRangeExtractor** - Never fails on boundaries
- **AccumulationNodeCompat** - Compatible with accumulation patterns

### Text Processing (2)
- **TextCleanup** - Flexible text cleaning
  - Operations: trim, unicode, newlines, collapse, ascii, etc.
  - Custom replacements with patterns
- **TextListCleanup** - Same for lists
  - Join with custom separators ("|" for WAN)
  - Maintains order

### Utilities (5)
- **PromptTemplateLoader** - Load prompt templates
  - Recursive search in templates/
  - YAML frontmatter support
- **LoopSafeAccumulator** - Original loop accumulator
- **VLMImagePassthrough** - Zero-copy image passthrough (no resizing, no copies)
  - Use when no preprocessing needed
  - Massive memory savings
- **VLMImageResizer** - Minimal resizer (only copies when actually resizing)
  - For when you need client-side resize
- **AdvancedVLMSampler** - Fine-tune generation parameters
  - top_k, repetition_penalty, etc.
  - Returns config for reuse
- **GlobalMemoryCleanup** - Comprehensive memory cleanup
  - Modes: light (caches), normal (+accumulators), aggressive (+gc), nuclear (+cuda)
  - Place before heavy operations or between workflow runs

### Creative & Encoding (2) - UPDATED!
- **RemoteTextEncoder** - Get real embeddings from heylookitsanllm
  - **IMPORTANT**: Requires heylookitsanllm to implement `/v1/embeddings` endpoint
  - Returns actual model embeddings (not hallucinated numbers)
  - Configurable dimensions (truncation support)
  - Batch processing support
  - Compatible with diffusion model conditioning
  - See docs/heylookllm_embeddings_spec.md for server implementation requirements
  - See docs/CREATIVE_FEATURES.md for usage details
- **SeedPromptGenerator** - Creative prompt seed generation
  - 5 categories: cinematic, artistic, narrative, conceptual, experimental
  - 4 variation modes: random, systematic, evolutionary, thematic
  - Custom templates and variables
  - AI enhancement option
  - Term filtering (avoid/prefer)
  - See docs/CREATIVE_FEATURES.md for examples

## Troubleshooting

### GetImageRangeFromBatch Errors
Replace with **ImageRangeExtractor** or **ImagePairIterator** depending on use case.

### OOM Errors
1. **Check for memory leaks first**:
   - Add GlobalMemoryCleanup node at workflow start
   - Set `cleanup_mode="nuclear"` for maximum cleanup
   - Check ShrugPrompter cache - set `use_cache=False` or `clear_cache=True`
   - Use `clear_all=True` on accumulators between runs
2. **Replace VLMImageProcessor with VLMImagePassthrough** - Avoids creating image copies
3. Use server-side resizing - Set resize parameters in ShrugPrompter:
   - `resize_mode="max"`, `resize_value=512`
4. Enable multipart endpoint - Automatically detected, 57ms faster per image
5. Set batch_mode=true for multi-image processing
6. Process fewer images at once
7. Use `reset=true` on LoopAwareVLMAccumulator to prevent buildup
8. Monitor cache stats in ShrugPrompter output

### Workflow Stuck at Frame Extraction
This usually means the batch structure changed. Use the new extraction nodes that handle edge cases better.

### ForLoop Not Executing
**Most common issue**: Ensure FLOW_CONTROL output from ForLoopOpen (output index 2) is connected to ForLoopClose input.

## Integration with heylookllm

Shrug-prompter nodes communicate with heylookllm server:
- Default endpoint: `http://localhost:8080`
- Supports both OpenAI and Ollama API formats
- Model example: `gemma3n-e4b-it` (fast, efficient VLM)
- **NEW**: Auto-detects server capabilities for optimal performance
- **NEW**: Uses multipart endpoint when available (57ms faster, 33% less bandwidth)
- **NEW**: Advanced server-side image resizing with multiple modes and quality options
- **IMPORTANT**: RemoteTextEncoder requires `/v1/embeddings` endpoint (see docs/heylookllm_embeddings_spec.md)

## File Structure
```
shrug-prompter/
├── nodes/                      # All node implementations
│   ├── image_pair_iterator.py  # Video interpolation nodes
│   ├── prompter.py            # Main VLM nodes
│   └── ...
├── example_workflows/          # Example JSON workflows
│   ├── video_interpolation_loop.json
│   ├── simple_batch_vlm.json
│   └── almost.json
├── templates/                  # Prompt templates
├── __init__.py                # Node registration
└── CLAUDE.md                  # This file
```

### Key Documentation
- `VIDEO_INTERPOLATION_GUIDE.md` - Complete guide for video workflows
- `fix_almost_workflow.md` - Specific fixes for complex workflows

## Common Issues and Solutions

### Issue: Video workflow processes only first frame pair
**Solution**: Ensure loop index from ForLoopOpen connects to ImagePairIterator's pair_index input

### Issue: Batch processing causes OOM
**Solution**: Use batch_mode=true in ShrugPrompter, add MemoryManager nodes

### Issue: GetImageRangeFromBatch fails with "index out of range"
**Solution**: Replace with ImagePairIterator for frame pairs or ImageRangeExtractor for simple ranges

### Issue: ForLoop doesn't iterate / workflow stuck
**Solution**: Connect FLOW_CONTROL (output 2) from ForLoopOpen to ForLoopClose

### Issue: Images not properly paired for interpolation
**Solution**: Use ImagePairIterator with proper pair_index from loop

### Issue: Leading spaces in VLM responses
**Solution**: Use `response_cleanup="standard"` in ShrugPrompter or TextCleanup node

### Issue: VLM returns JSON but you need plain text
**Solution**: ShrugPrompter automatically parses common JSON formats, extracts prompts

### Issue: Accumulator shows duplicate contexts
**Solution**: Set `reset=true` on LoopAwareVLMAccumulator or use unique accumulator_id

## Example Fix for "almost.json" Workflow

The workflow should now work automatically with our backward compatibility mappings:

1. **GetImageRangeFromBatch** (node 833) → Automatically replaced with `RobustImageRangeExtractor`
2. **BatchVLMAccumulator** → Automatically replaced with `LoopAwareVLMAccumulator`
3. **BatchVLMResponseIterator** → Automatically replaced with `LoopAwareResponseIterator`
4. **VLMImageOptimizer** → Automatically replaced with `VLMImageProcessor`

### To improve the workflow further:

1. Add **AutoMemoryManager** after heavy operations:
```json
{
  "type": "AutoMemoryManager",
  "inputs": [{"name": "trigger", "link": <previous_output>}],
  "widgets_values": ["aggressive", 1000]
}
```

2. The workflow now handles edge cases automatically:
- Image extraction won't fail even if indices are out of bounds
- VLM accumulation works properly inside the ForLoop
- Memory is managed automatically

## Development Guidelines

### Adding New Nodes
1. Create node file in `nodes/` directory
2. Import in `__init__.py`
3. Add to NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS
4. Follow existing patterns for inputs/outputs

### Testing Workflows
1. Start with minimal examples (2-3 images)
2. Add ShowText nodes for debugging
3. Monitor with debug_info outputs
4. Check memory usage frequently
5. Verify ForLoop connections

### Best Practices
- Always provide debug_info outputs
- Handle edge cases (empty batches, single images)
- Include clear docstrings and type hints
- Test with various model providers
- Document ForLoop requirements clearly
- Use VLMImagePassthrough for zero-copy when possible
- Enable response_cleanup for downstream compatibility
- Set batch_mode=true for multiple images
- Reset accumulators between workflow runs

## WAN VACE Integration

For detailed WAN VACE workflow integration, see the extensive documentation below. The key points:
- Use loop-based VLM processing for scalability
- Pre-generate all prompts in Phase 0 before video generation
- Preserve all Anything Everywhere nodes and workflow structure
- Single VLM node in a loop is better than multiple VLM nodes

---

# Original WAN VACE Integration Guide

[The rest of the original CLAUDE.md content follows here...]

## Overview
This guide helps integrate the shrug-prompter VLM system into the reference WAN VACE workflow (`ref_workflow.json`). The goal is to replace manual prompt entry with automated VLM-based prompt generation while preserving the sophisticated video generation architecture.

## Critical Architecture Understanding

### Reference Workflow Pattern
The reference workflow (`example_workflows/ref_workflow.json`) uses a **pre-generation pattern**:

1. **Phase 0**: ALL prompts are generated/defined BEFORE any video generation
2. **Storage**: Prompts stored in accumulator via `MakeListNode` → `ListToAccumulationNode`
3. **Retrieval**: Loop uses `AccumulationGetItemNode` to fetch prompts by index
4. **Globals**: Extensive use of "Anything Everywhere" nodes for width, height, steps, etc.

### Current Manual Process
```
PrimitiveStringMultiline (x5) → MakeListNode → ListToAccumulationNode → Accumulator
                                                                              ↓
ForLoopOpen → AccumulationGetItemNode (index) → WanVideoTextEncode → Video Generation
```

## Integration Strategy

### Replace Manual Prompts with VLM Loop
The integration creates a new Phase 0 loop that generates all prompts before video generation. This is the optimal approach:

```
IMPORTANT: Use a LOOP for VLM processing, not multiple VLM nodes!

Phase 0 VLM Loop:
LoadImages → ImpactMakeImageList → ListToAccumulationNode → IMAGE Accumulator
                                                                   ↓
                   ForLoopOpen → AccumulationGetItemNode → ShrugPrompter
                                       (keyframe[i])             ↓
                                                           ResponseParser
                                                                   ↓
                                                         AccumulationNode
                                                        (STRING Accumulator)
                                                                   ↓
                                                     Anything Everywhere

Shared nodes (single instance):
- ShrugProviderSelector (VLM context)
- PromptTemplateLoader_Shrug (template)
- User prompt instruction
- Single ShrugPrompter in the loop
```

## Key Implementation Details

### 1. VLM Prompt Generation Setup
```python
# Nodes to add in Phase 0:
- ShrugProviderSelector: Configure local qwen2.5-vl server
- PromptTemplateLoader_Shrug: Load "wan_prompt_rewriter_qwen.md"
- ImpactMakeImageBatch: Combine all keyframes into single batch
- ShrugPrompter: Single API call with ALL keyframes
- EnhancedResponseParser: Extract array of prompts
```

### 2. Template Selection
Use `wan_prompt_rewriter_qwen.md` because:
- Designed specifically for WAN VACE video generation
- Analyzes actual image content (grounded prompts)
- Outputs cinematic descriptions suitable for video
- One prompt per keyframe (not per transition)

### 3. Handling Prompt Counts
**Problem**: `MakeListNode` has only 9 input slots but you may have more keyframes.

**Solutions**:
```python
# Option A: Use DynamicPromptAccumulator (if available)
EnhancedResponseParser → prompts_array → DynamicPromptAccumulator → accumulator

# Option B: Direct array handling
EnhancedResponseParser → prompts_array → Custom converter → individual strings

# Option C: Modify to handle dynamic counts
Use multiple MakeListNodes or create custom accumulator node
```

### 4. Critical Nodes to Preserve
- ALL "Anything Everywhere" nodes (globals distribution)
- Fast Groups Muter (phase control)
- ForLoopOpen/ForLoopClose structure
- AccumulationGetItemNode for prompt retrieval
- WanVideoContextOptions (missing from many workflows!)
- All existing video generation nodes

## Node Connection Map

### Phase 0 Modifications
```
# Remove/Disconnect:
- PrimitiveStringMultiline nodes (705, 706, 707, 708)

# Add:
1. After keyframe loading:
   LoadImage → ImpactMakeImageBatch → batch_output

2. VLM setup:
   ShrugProviderSelector → context
   PromptTemplateLoader_Shrug → template

3. VLM processing:
   context + template + batch_output → ShrugPrompter → updated_context
   updated_context → EnhancedResponseParser → prompts_array

4. Connect to existing:
   prompts_array → [split into individual strings] → MakeListNode inputs
```

### Keep Intact
- ForLoop structure (nodes 635, 636)
- AccumulationGetItemNode (node 719)
- WanVideoTextEncode (node 168)
- All video generation nodes

## Common Pitfalls to Avoid

### 1. Wrong Prompting Pattern
❌ Generating prompts during loop iteration
✅ Pre-generating ALL prompts before loop starts

### 2. Wrong Prompt Type
❌ Transition prompts (between keyframes)
✅ Individual keyframe descriptions

### 3. Missing Context
❌ Removing WanVideoContextOptions
✅ Keep context options for sliding window processing

### 4. Breaking Globals
❌ Removing "Anything Everywhere" nodes
✅ Preserve all global parameter distribution

## Technical Parameters

### Optimal Settings
```python
# VLM call:
max_tokens: 150-200 per keyframe
temperature: 0.7
top_p: 0.9

# WAN generation:
num_frames: 81 (optimal for training)
context_frames: 81
stride: 4
overlap: 16-32
schedule: "uniform_standard"
```

### Frame Calculations
- 3 keyframes = 2 transitions = 2 loop iterations
- 5 keyframes = 4 transitions = 4 loop iterations
- N keyframes = N-1 transitions

## Example User Prompt for VLM
```
Analyze this keyframe image and create a detailed, cinematic prompt
for WAN VACE video generation. This prompt will be used to generate
a video transition FROM this keyframe TO the next one. Focus on:

- What action or movement could naturally occur starting from this frame
- Subject appearance and current pose/position
- Suggested movement or action that leads to the next frame
- Environment details and camera work
- Mood and atmosphere

Output only the prompt text, no JSON or formatting.
```

## Shrug-Prompter Node Details

### Available Nodes
From `/nodes/__init__.py`:
- `ShrugPrompter` - Main VLM API caller
- `ShrugProviderSelector` - Configure VLM provider (local server)
- `ShrugResponseParser` - Basic response parser
- `EnhancedResponseParser` - Handles array responses
- `PromptTemplateLoader_Shrug` - Load prompt templates
- `DynamicPromptAccumulator` - Alternative to MakeListNode
- `AccumulationToList` - Convert accumulator to list
- `SmartAccumulationNode` - All-in-one accumulation operations

### Implementation Notes

1. **Loop-based approach** is superior to multiple VLM nodes
2. **Accumulation pattern** scales to any number of keyframes
3. **Single VLM prompter** processes one keyframe per loop iteration
4. The VLM returns one prompt per call:
   ```
   "A woman in red dress standing in moonlight, beginning to turn..."
   ```

5. Each prompt describes action/transition FROM that keyframe

### Connection Example
```
# For any N keyframes (scalable):
LoadImages → ImpactMakeImageList → ListToAccumulationNode
                                           ↓
                                   IMAGE Accumulator
                                           ↓
             ForLoop(N times): Get[i] → VLM → Parse → Accumulate
                                                          ↓
                                                  STRING Accumulator
                                                          ↓
                                                Anything Everywhere
```

## Testing Checklist

- [ ] Phase 0 loop runs N times for N keyframes
- [ ] Each iteration processes one keyframe
- [ ] VLM generates one prompt per iteration
- [ ] All prompts accumulate properly
- [ ] Anything Everywhere broadcasts accumulator
- [ ] Phase 2 loop retrieves prompts by correct index
- [ ] Video generation uses proper prompt for each segment
- [ ] Final output maintains temporal coherence

## File Locations
- Reference workflow: `/example_workflows/ref_workflow.json`
- Templates: `/templates/wan_prompt_rewriter_qwen.md`
- Shrug nodes: `/nodes/` (prompter.py, response_parser.py, etc.)
- Example workflows: `/example_workflows/` (various attempts)

## Debugging Tips

1. **Check VLM Response**: Add debug nodes after ShrugPrompter to see raw response
2. **Verify Parser Output**: EnhancedResponseParser should output array of strings
3. **Count Prompts**: Ensure N keyframes → N prompts (not N-1)
4. **Index Alignment**: AccumulationGetItemNode uses 0-based indexing
5. **Template Issues**: If prompts are too short/long, adjust template or max_tokens

## Next Steps
1. Load `ref_workflow.json`
2. Identify Phase 0 prompt section (nodes 697-708)
3. Insert VLM nodes between keyframes and MakeListNode
4. Test with 3 keyframes first
5. Scale to more keyframes using dynamic accumulator if needed

## Example Workflow Modifications

### Before (Manual):
```json
{
  "id": 706,
  "type": "PrimitiveStringMultiline",
  "widgets_values": ["A woman doing squats"]
}
```

### After (VLM):
```json
{
  "id": 706,
  "type": "ShrugPrompter",
  "inputs": [
    {"name": "context", "link": <from_provider>},
    {"name": "images", "link": <from_batch>},
    {"name": "system_prompt", "link": <from_template>}
  ]
}
```

Remember: The goal is minimal disruption to the existing workflow while adding intelligent prompt generation.

## Quick Reference Diagram

```
REFERENCE WORKFLOW (Manual):
┌─────────────┐
│   Phase 0   │ PrimitiveStringMultiline (x5) → MakeListNode → Accumulator
└─────────────┘
┌─────────────┐
│   Phase 2   │ ForLoop → AccumulationGetItemNode → TextEncode → VideoGen
└─────────────┘

SHRUG-PROMPTER INTEGRATION:
┌─────────────┐
│   Phase 0   │ Keyframes → VLM → Parse → MakeListNode → Accumulator
└─────────────┘                    ↑
                           Smart prompting here
┌─────────────┐
│   Phase 2   │ [UNCHANGED] Same loop structure
└─────────────┘
```

## TL;DR for Next Claude

1. **DON'T** generate prompts during the loop
2. **DO** pre-generate all prompts in Phase 0
3. **DON'T** remove any existing nodes except manual prompts
4. **DO** preserve all globals and workflow structure
5. **USE** `wan_prompt_rewriter_qwen.md` template
6. **EXPECT** one prompt per keyframe (not per transition)
7. **USE** looping pattern for VLM (not multiple VLM nodes)

The reference workflow is sophisticated - respect its architecture and only modify the prompt generation part.

## FINAL SOLUTION: Looping VLM Architecture

After multiple iterations, the cleanest solution uses a **looping pattern** for VLM prompt generation that mirrors the video generation loop:

### Phase 0 VLM Loop (NEW)
```
Keyframes → MakeImageList → ListToAccumulation → Accumulator
                                                       ↓
ForLoopOpen (0 to N-1) → AccumulationGetItem → VLM → Parser → AccumulationNode
                             (keyframe[i])                          ↓
                                                           Prompt Accumulator
                                                                    ↓
                                                       Anything Everywhere
```

### Phase 2 Video Loop (UNCHANGED)
```
ForLoopOpen → AccumulationGetItem → WanVideoTextEncode → Video Generation
                (prompt[i])
```

### Key Benefits
- **Single VLM node** instead of N separate chains
- **Scalable** to any number of keyframes
- **Clean architecture** matching reference pattern
- **Proper accumulation** for both keyframes and prompts

### Final Workflow
**File**: `example_workflows/wan-vace-shrug-looping-final.json`

This uses the same accumulation and looping patterns as the reference workflow, just applied to VLM prompt generation in Phase 0.

## Complete Integration Implementation

### Created Workflows

1. **wan-vace-shrug-looping-final.json** - OPTIMAL IMPLEMENTATION ✅
   - Loop-based VLM processing (single VLM node)
   - Scalable to any number of keyframes
   - Clean accumulation pattern
   - Phase 0 ForLoop for prompt generation
   - Fast Groups Muter properly configured
   - All 34 "Anything Everywhere" nodes preserved
   - Mirrors reference workflow architecture

2. **Previous working versions** (less optimal):
   - wan-vace-shrug-fixed-final.json - Multiple VLM nodes approach
   - wan-vace-shrug-ultimate-final-v2.json - 7 VLM nodes version

3. ~~Failed attempts~~ - See workflow evolution below

### Integration Scripts

Created Python scripts in `/scripts/` to automate the integration:

**Looping Solution Scripts:**
- `create_looping_vlm_workflow.py` - Creates clean loop-based VLM workflow
- `fix_looping_workflow.py` - Fixes loop counts and adds documentation
- `validate_looping_workflow.py` - Validates the looping architecture

**Previous Approach Scripts:**
- `create_complete_workflow.py` - Creates workflow with multiple VLM nodes
- `fix_workflow_issues.py` - Fixes critical issues (muter config, loop index, etc.)
- `deep_workflow_analysis.py` - Deep analysis to find issues
- `final_validation.py` - Comprehensive validation of workflows
- `verify_workflow_integrity.py` - Verifies all critical components are preserved
- `diagnose_workflow.py` - Diagnostic tool for debugging connections
- `comprehensive_reanalysis.py` - Re-analyzes workflow logic
- `final_comprehensive_fix.py` - Attempts to fix all issues
- `ultimate_thorough_fix.py` - Final fix for multiple VLM approach

### Key Implementation Details

The integration preserves ALL 7,349 lines of the reference workflow including:
- 34 "Anything Everywhere" nodes for global parameters
- Complete WAN video model loading chain
- ForLoopOpen/ForLoopClose structure (nodes 635, 636)
- AccumulationGetItemNode (node 719) for prompt retrieval
- WanVideoContextOptions (node 727) - critical for sliding window
- All video generation nodes (sampler, encoder, decoder)

### Integration Points

**Nodes Removed:**
- PrimitiveStringMultiline nodes (IDs: 704, 705, 706, 707, 708, 721)
- MakeListNode (ID: 697) - replaced by accumulation pattern
- ListToAccumulationNode (ID: 698) - replaced by new accumulator

**Nodes Added (Loop-based approach):**
1. **Phase 0 VLM Setup:**
   - ShrugProviderSelector - Configures local qwen2.5-vl server
   - PromptTemplateLoader_Shrug - Loads wan_prompt_rewriter_qwen.md
   - PrimitiveNode - User prompt instruction

2. **Phase 0 Keyframe Collection:**
   - ImpactMakeImageList - Collects all keyframes into list
   - ListToAccumulationNode - Creates IMAGE accumulator

3. **Phase 0 Loop Components:**
   - ForLoopOpen/Close - Phase 0 loop (N iterations)
   - AccumulationGetItemNode - Gets keyframe[i] each iteration
   - ShrugPrompter - Single VLM node (processes one keyframe per iteration)
   - ShrugResponseParser - Extracts prompt text
   - AccumulationNode - Collects prompts into STRING accumulator

4. **Execution Trigger:**
   - PreviewImage - Creates demand for Phase 0 execution

### Workflow Comparison

**Original Manual Flow:**
```
LoadImage1 → [Manual typing] → PrimitiveStringMultiline1 ↘
LoadImage2 → [Manual typing] → PrimitiveStringMultiline2 → MakeListNode → ListToAccumulationNode
LoadImage3 → [Manual typing] → PrimitiveStringMultiline3 ↗
```

**OPTIMAL VLM Flow (Loop-based):**
```
LoadImages → ImpactMakeImageList → ListToAccumulationNode → IMAGE Accumulator
                                                                   ↓
               ForLoop: AccumulationGetItemNode → ShrugPrompter → ResponseParser
                             ↓                                           ↓
                       keyframe[i]                                AccumulationNode
                                                                        ↓
                                                              STRING Accumulator

Each keyframe still gets its own VLM processing, but via a clean loop!
```

### Critical Architecture Rules

**1. EACH KEYFRAME GETS INDIVIDUAL VLM PROCESSING**
- The VLM cannot batch-analyze multiple images for separate prompts
- Solution: Process one keyframe per loop iteration

**2. USE LOOPS, NOT MULTIPLE NODES**
- Instead of N ShrugPrompter nodes, use 1 node in a loop
- Scales automatically to any number of keyframes
- Follows ComfyUI best practices

**3. ACCUMULATION PATTERN**
- Input: IMAGE accumulator stores all keyframes
- Output: STRING accumulator collects all prompts
- Enables clean indexed access in both loops

### Critical Issues Resolved

1. **Fast Groups Muter Configuration**: Must be properly configured
   - One muter set to "" (empty) to show all groups
   - Other can default to "Phase 0"
   - Without configuration, phase control doesn't work!

2. **AccumulationGetItemNode Index**: MUST connect to ForLoop
   - Static index of 0 means only first prompt is used
   - Must receive dynamic index from ForLoopOpen
   - Connection: ForLoopOpen output 1 → AccumulationGetItemNode input 0

3. **Execution Trigger**: PreviewImage creates demand
   - ComfyUI uses demand-driven execution
   - PreviewImage in Phase 0 forces VLM execution
   - Must be connected to a keyframe image

### Execution Instructions

1. **Start Local VLM Server**:
   ```bash
   # Ensure qwen2.5-vl is running at http://localhost:8080
   ```

2. **Load Workflow**:
   - Open ComfyUI
   - Load `wan-vace-shrug-fixed-final.json`

3. **Execute Phase 0** (Generate Prompts):
   - Set Fast Groups Muter to "Phase 0"
   - Queue prompt
   - VLM will analyze keyframes and generate prompts

4. **Execute Main Workflow** (Generate Video):
   - Switch Fast Groups Muter to empty or "Phase Rest of Them"
   - Queue prompt again
   - Video generation will use VLM-generated prompts

### Key Learnings

1. **Demand-Driven Execution**: Nodes only execute if something downstream demands their output
2. **Phase Control**: Fast Groups Muter must be configured, not just present
3. **Dynamic Indexing**: Loop variables must be connected, not static
4. **Complete Removal**: Don't just bypass nodes - remove them completely
5. **Execution Order**: Use `order` property to ensure proper sequencing
