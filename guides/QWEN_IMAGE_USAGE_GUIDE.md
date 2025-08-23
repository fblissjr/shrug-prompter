# Qwen-Image Usage Guide

Complete guide for using qwen-image edit model with the provided templates.

## Quick Start

### 1. Basic Edit Command
```python
# Simple text addition
edit = 'Add text "SALE" in red at top-right corner'

# Object replacement  
edit = 'Replace the blue car with a red motorcycle'

# Background change
edit = 'Change background to sunset beach scene'
```

### 2. System Prompts (Choose One)

**Descriptive Mode:**
```
Describe the image by detailing the color, shape, size, texture, quantity, text, spatial relationships of the objects and background:
```

**Edit Instruction Mode:**
```
Describe the key features of the input image, then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input
```

## Template Selection Guide

### Which Template to Use?

| Use Case | Template | Best For |
|----------|----------|----------|
| Quick edits | `qwen_image_simple_prompts.md` | Single operations, fast processing |
| Precise control | `qwen_image_structured_schemas.md` | Complex edits with exact specifications |
| Professional rewriting | `qwen_image_edit_rewriter.md` | Converting vague instructions to precise ones |
| Multiple images | `qwen_image_batch_processor.md` | Consistent edits across image sets |
| Learning examples | `qwen_image_diverse_examples.md` | Understanding edit patterns |
| Detailed structure | `qwen_image_edit_structured.md` | Multi-step complex edits |
| Chinese editing | `qwen_image_photo_edit_zh.md` | 中文照片编辑指令 |
| English→Chinese | `qwen_image_en_to_zh.md` | Bilingual workflow support |
| DiffSynth bridge | `qwen_image_diffsynth_bridge.md` | Integration with DiffSynth-Studio |

## Common Workflows

### Workflow 1: E-commerce Product Enhancement

```python
# Step 1: Load product image
image = load_image("product.jpg")

# Step 2: Apply structured schema
schema = {
    "operation": "composite_edit",
    "edits": [
        {"action": "remove", "target": "background"},
        {"action": "add", "element": "white background"},
        {"action": "add", "element": '"NEW" badge', "position": "top-left"},
        {"action": "adjust", "property": "brightness", "value": "+10%"}
    ]
}

# Step 3: Process
result = qwen_image_edit(image, schema)
```

### Workflow 2: Social Media Batch Processing

```python
# Using batch processor template
batch_config = {
    "operation": "add_watermark",
    "watermark": {
        "text": "@photographer",
        "position": "bottom-right",
        "opacity": 50,
        "color": "white"
    },
    "apply_to": "all_images"
}

# Process folder
for image in image_folder:
    process_with_template(image, batch_config)
```

### Workflow 3: Text Overlay with Validation

```python
# Using rewriter for clarity
vague_instruction = "put some text on the image"

# Rewrite to precise instruction
precise_instruction = rewrite_instruction(
    vague_instruction,
    template="qwen_image_edit_rewriter"
)
# Result: 'Add text "Sample Text" in black at center with 24px font size'

# Apply edit
edited = qwen_image_edit(image, precise_instruction)
```

## Best Practices

### 1. Instruction Clarity

**❌ Poor:**
```
"make it better"
"fix the image"
"add something"
```

**✅ Good:**
```
"Increase brightness by 20% and add slight contrast"
"Remove person in blue shirt from left side"
"Add red 'SALE' badge at top-right corner"
```

### 2. Text Handling

**Always Quote Text:**
```python
# Wrong
edit = "Add text Hello World at top"

# Correct
edit = 'Add text "Hello World" at top'
```

**Preserve Original Language:**
```python
# Wrong (translating)
edit = 'Replace "你好" with "Hello"'

# Correct (preserving)
edit = 'Replace "你好" with "世界"'
```

### 3. Position Specification

**Position Grid:**
```
top-left    | top-center    | top-right
left        | center        | right
bottom-left | bottom-center | bottom-right
```

**Precise Positioning:**
```python
# Basic
position = "top-right"

# Detailed
position = {
    "x": "50px from right",
    "y": "30px from top"
}

# Relative
position = "10% from left, 20% from top"
```

### 4. Color Specification

**Methods:**
```python
# Named colors
color = "red"

# Hex codes
color = "#FF5733"

# RGB
color = "rgb(255, 87, 51)"

# With opacity
color = "rgba(255, 87, 51, 0.8)"
```

## Advanced Techniques

### 1. Multi-Step Edits

```python
# Sequential processing
steps = [
    "Remove background",
    "Add white background",
    'Add text "Product Name" at top',
    "Add shadow to product",
    "Adjust lighting to bright"
]

for step in steps:
    image = qwen_image_edit(image, step)
```

### 2. Conditional Edits

```python
# Using structured schema
conditional_edit = {
    "if": {"image_brightness": "< 30%"},
    "then": {"action": "increase_brightness", "value": "+40%"},
    "else": {"action": "maintain_current"}
}
```

### 3. Style Preservation

```python
# Maintain consistency
edit_with_preservation = {
    "edit": "Change shirt color to blue",
    "preserve": [
        "lighting",
        "shadows",
        "texture",
        "wrinkles",
        "overall style"
    ]
}
```

## Error Handling

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Text not visible | Specify contrasting color or add background |
| Object placement overlaps | Use precise coordinates |
| Style mismatch | Add "maintain original style" |
| Quality degradation | Use higher resolution input |
| Edit not applied | Simplify instruction, check format |

### Validation Checklist

Before sending edit instruction:
- [ ] Text content in quotes
- [ ] Position specified
- [ ] Colors defined (if needed)
- [ ] Size/scale mentioned (if needed)
- [ ] Preservation context stated
- [ ] No conflicting instructions
- [ ] Under 50 words

## Performance Optimization

### 1. Batch Processing
```python
# Efficient batch handling
def batch_edit(images, edit_instruction):
    results = []
    # Process in parallel if possible
    for img in images:
        results.append(qwen_image_edit(img, edit_instruction))
    return results
```

### 2. Template Caching
```python
# Pre-load templates
templates = {
    'watermark': load_template('watermark_schema.yaml'),
    'text_overlay': load_template('text_overlay_schema.yaml'),
    'style_transfer': load_template('style_transfer_schema.yaml')
}

# Reuse templates
result = apply_template(image, templates['watermark'])
```

### 3. Resolution Management
```python
# Optimize for processing
if image.width > 2048:
    image = resize_maintain_aspect(image, max_width=2048)
    
# Process edit
edited = qwen_image_edit(image, instruction)

# Upscale if needed
if original_was_larger:
    edited = upscale_to_original(edited, original_dimensions)
```

## Integration Examples

### ComfyUI Integration
```python
class QwenImageEditNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "instruction": ("STRING", {"multiline": True}),
                "template": (["simple", "structured", "schema"],),
            }
        }
    
    def edit_image(self, image, instruction, template):
        # Load appropriate template
        template_content = load_template(f"qwen_image_{template}.md")
        
        # Process edit
        return qwen_edit_with_template(image, instruction, template_content)
```

### API Integration
```python
def api_edit_endpoint(image_path, edit_instruction):
    # Load image
    image = load_image(image_path)
    
    # Validate instruction
    validated = validate_instruction(edit_instruction)
    
    # Apply edit
    result = qwen_image_edit(image, validated)
    
    # Return result
    return save_and_return(result)
```

## Testing Your Edits

### Test Suite Examples
```python
test_cases = [
    # Text addition
    {'edit': 'Add text "TEST" at center', 'expected': 'text visible at center'},
    
    # Object removal
    {'edit': 'Remove all people', 'expected': 'no people in result'},
    
    # Style change
    {'edit': 'Make image sepia toned', 'expected': 'brown/vintage coloring'},
    
    # Complex edit
    {'edit': 'Add border, watermark, and adjust brightness', 'expected': 'all three changes visible'}
]
```

## Troubleshooting

### Debug Mode
```python
def debug_edit(image, instruction):
    print(f"Original instruction: {instruction}")
    
    # Rewrite for clarity
    clear_instruction = rewrite_instruction(instruction)
    print(f"Clarified: {clear_instruction}")
    
    # Parse components
    components = parse_instruction(clear_instruction)
    print(f"Components: {components}")
    
    # Apply edit with verbose output
    result = qwen_image_edit(image, clear_instruction, verbose=True)
    
    return result
```

## Resources

- **Analysis Document**: `QWEN_IMAGE_ANALYSIS.md` - Dataset patterns and insights
- **Templates Folder**: `/templates/qwen_image_*.md` - All available templates
- **Examples**: `qwen_image_diverse_examples.md` - 30+ practical examples
- **Schemas**: `qwen_image_structured_schemas.md` - Detailed attribute schemas
- **Chinese Templates**: 
  - `qwen_image_photo_edit_zh.md` - Complete Chinese photo editing guide
  - `qwen_image_en_to_zh.md` - English to Chinese translation patterns
  - `qwen_image_diffsynth_bridge.md` - DiffSynth-Studio integration

## Summary

1. **Start Simple**: Use `qwen_image_simple_prompts.md` for basic edits
2. **Be Precise**: Always specify position, size, color when relevant
3. **Quote Text**: All text content must be in quotes
4. **Preserve Context**: Explicitly state what should remain unchanged
5. **Test Incrementally**: For complex edits, test each step separately
6. **Use Templates**: Leverage provided templates for consistency
7. **Validate Input**: Check instruction format before processing

With these templates and guidelines, you can effectively use qwen-image for a wide range of image editing tasks with predictable, high-quality results.