# Qwen-Image System Prompts Guide

Guide for using the streamlined system prompts with Qwen2.5-VL and other vision language models.

## Overview

System prompts are the actual instructions given to the VLM to transform user input. Unlike guides (which are for humans), system prompts must be:
- **Concise and direct**
- **Grounded in dataset patterns**
- **Executable by the model**
- **Free from explanatory content**

## Available System Prompts

### 1. General Edit Rewriter
**File**: `qwen_image_system_rewriter.md`
**Purpose**: Transform vague user instructions into precise edit commands
**Key Features**:
- Single-line output format
- Dataset pattern adherence
- Image-grounded descriptions
- Precision requirements

**Usage Example**:
```python
system_prompt = load_template("qwen_image_system_rewriter.md")
user_input = "make it look better"
image = load_image("photo.jpg")

# Model analyzes image and outputs:
"Increase brightness by 15% and enhance contrast, preserve skin tones"
```

### 2. Multi-Person Compositor
**File**: `qwen_image_system_multi_person.md`
**Purpose**: Combine multiple people from different images
**Key Features**:
- Identity preservation protocol
- Explicit person identification
- Feature lock requirements
- Scene integration rules

**Usage Example**:
```python
system_prompt = load_template("qwen_image_system_multi_person.md")
images = [portrait1, portrait2]
user_input = "put them at a beach"

# Model outputs:
"Combine Person 1 (asian woman, black hair) from first image and 
Person 2 (blonde woman) from second image standing on beach, 
preserving exact facial features"
```

### 3. Multi-Source Element Merger
**File**: `qwen_image_system_multi_source.md`
**Purpose**: Merge specific elements from multiple source images
**Key Features**:
- Element extraction protocol
- Preservation hierarchy
- Adaptive element handling
- Natural blending requirements

**Usage Example**:
```python
system_prompt = load_template("qwen_image_system_multi_source.md")
images = [face_photo, armor_design, forest_background]
user_input = "combine these elements"

# Model outputs:
"Integrate woman from image 1 preserving exact facial features, 
wearing armor from image 2, in forest from image 3"
```

## System Prompt Structure

All system prompts follow this structure:

```yaml
---
output_type: single_string
description: "Purpose of the prompt"
model_requirements: "vision_capable"
---
# Instructions
[Direct instructions to the model]

## Core Directives
[Main rules to follow]

## Output Structure
[Format requirements]

## Examples
[Input/output patterns]

# Output ONLY [specific requirement]
```

## Dataset-Grounded Patterns

Based on qwen-image dataset analysis, all system prompts enforce:

### Text Handling
- Always quote text: "SALE 50% OFF"
- Never translate text
- Preserve capitalization

### Spatial Precision
- Use quadrant system: top-left, center, bottom-right
- Specify percentages: "20% from left"
- Define pixels: "100px width"

### Color Specification
- Named colors with hex: "red (#FF0000)"
- Preserve exact tones when specified
- Include opacity when relevant

### Size Definition
- Pixels for absolute: "48px font"
- Percentages for relative: "15% of image width"
- Maintain proportions

## Integration with ComfyUI

### Using System Prompts in Nodes

```python
class QwenImageRewriter:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "user_instruction": ("STRING",),
                "system_prompt": (["rewriter", "multi_person", "multi_source"],),
            }
        }
    
    def process(self, image, user_instruction, system_prompt):
        # Load appropriate system prompt
        template = f"qwen_image_system_{system_prompt}.md"
        prompt = load_template(template)
        
        # VLM processes with system prompt
        result = vlm_process(image, user_instruction, prompt)
        
        return (result,)
```

## Key Differences from Guides

### System Prompt (Actual Template)
```
# Instructions
You rewrite image edit instructions. Analyze the image and output precise commands.

## Rules
Text in quotes. Positions as quadrants. Colors with hex codes.

## Examples
Input: "add text"
Output: Add text "Sample" in black at center

# Output ONLY the rewritten instruction.
```

### Guide (Documentation)
```
# How to Use This Template

This template helps you understand how to write better instructions...

## Background Information
The qwen-image model was trained on...

## Tips and Tricks
- Try to be specific
- Consider the composition
[etc...]
```

## Best Practices

### DO:
- Keep system prompts under 500 words
- Use imperative voice ("Transform", "Analyze", "Generate")
- Include concrete examples
- End with output-only directive

### DON'T:
- Include explanations or background
- Use conditional language ("you might want to")
- Add tips or suggestions
- Include meta-commentary

## Prompt Selection Logic

```python
def select_system_prompt(task_type):
    if task_type == "edit_instruction":
        return "qwen_image_system_rewriter.md"
    elif task_type == "combine_people":
        return "qwen_image_system_multi_person.md"
    elif task_type == "merge_elements":
        return "qwen_image_system_multi_source.md"
    else:
        return "qwen_image_system_rewriter.md"  # default
```

## Performance Optimization

### Token Efficiency
System prompts are optimized for minimal token usage:
- Rewriter: ~400 tokens
- Multi-person: ~350 tokens
- Multi-source: ~380 tokens

### Processing Speed
Streamlined prompts enable:
- Faster inference
- More consistent outputs
- Better instruction following

## Validation

System prompts include validation through:
- Explicit output format requirements
- Clear examples of transformation
- Precision specifications
- Error prevention rules

## Migration from Old Templates

### Old Template Style:
```
This template is for combining multiple people...
Here's how you should think about it...
Consider these factors...
```

### New System Prompt Style:
```
You combine people from different images.
Preserve each person's identity.
Output format: [specific pattern]
```

## Summary

System prompts are:
1. **Direct instructions** to the VLM
2. **Pattern-based** from dataset analysis
3. **Output-focused** with clear format requirements
4. **Concise** without explanatory content
5. **Grounded** in observable image features

Use guides for understanding, system prompts for execution.