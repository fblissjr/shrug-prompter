# Qwen-Image Templates Overview

Complete guide to all qwen-image templates and their proper usage.

## Template Categories

### 1. System Prompts (For VLM Direct Use)

These templates are actual prompts that can be fed directly to a vision language model like Qwen2.5-VL:

#### Core System Prompts
- **`qwen_image_system_rewriter_v2.md`** - Main instruction optimizer (no dataset references)
- **`qwen_image_system_rewriter_fewshot.md`** - Extensive few-shot examples version
- **`qwen_image_system_dataset_grounded.md`** - Dataset-pattern based examples
- **`qwen_image_system_multi_person.md`** - Multi-person composition specialist
- **`qwen_image_system_multi_source.md`** - Multi-source element merger
- **`qwen_image_system_specialist.md`** - Domain-specific specialist (ecommerce, document, etc.)

#### Legacy System Prompts (Still Functional)
- `qwen_image_edit_rewriter.md` - Original rewriter
- `qwen_image_observation.md` - Image analysis and planning
- `qwen_image_rewriter_simple.md` - Simplified rewriter
- `qwen_image_batch_simple.md` - Batch processing
- `qwen_image_identity_preserve.md` - Identity preservation
- `qwen_image_professional_retouch.md` - Photo retouching
- `qwen_image_body_contouring.md` - Body enhancement
- `qwen_image_lighting_curves.md` - Lighting specialist
- `qwen_image_ecommerce.md` - E-commerce optimizer
- `qwen_image_document.md` - Document processor
- `qwen_image_real_estate.md` - Real estate editor
- `qwen_image_artistic.md` - Artistic transformer
- `qwen_image_edit_instruction.md` - Edit instruction specialist

### 2. Documentation/Guides (For Human Reference)

These are guides and documentation, not meant for direct VLM use:

- `qwen_image_diverse_examples.md` - Example collection
- `qwen_image_structured_schemas.md` - Schema documentation
- `qwen_image_simple_prompts.md` - Quick reference templates
- `qwen_image_batch_processor.md` - Batch processing guide
- `qwen_image_edit_structured.md` - Structured editing guide
- `qwen_image_multi_source_composition.md` - Composition guide
- `qwen_image_multi_person.md` - Multi-person guide

### 3. Bilingual/Special Templates

Templates for Chinese language and DiffSynth integration:

- `qwen_image_en_to_zh.md` - English to Chinese translation
- `qwen_image_photo_edit_zh.md` - Chinese photo editing
- `qwen_image_chinese_diffsynth.md` - DiffSynth Chinese integration
- `qwen_image_english_diffsynth.md` - DiffSynth English integration
- `qwen_image_diffsynth_bridge.md` - DiffSynth bridge
- `qwen_image_entity_control_diffsynth.md` - Entity control for DiffSynth

## Usage Guidelines

### For System Prompts

System prompts should:
1. **Not reference the model or dataset** - The VLM doesn't know what "qwen-image" is
2. **Be direct and instructional** - Use imperative voice
3. **Include clear output format** - End with "Output ONLY..."
4. **Be concise** - Under 500 words ideally
5. **Include examples** - Show transformation patterns

### Choosing the Right System Prompt

```python
def select_prompt(task, complexity):
    if complexity == "simple":
        return "qwen_image_system_rewriter_v2.md"
    elif complexity == "needs_examples":
        return "qwen_image_system_dataset_grounded.md"
    elif task == "multi_person":
        return "qwen_image_system_multi_person.md"
    elif task == "merge_elements":
        return "qwen_image_system_multi_source.md"
    elif task in ["ecommerce", "document", "realestate"]:
        return "qwen_image_system_specialist.md"
    else:
        return "qwen_image_system_rewriter_fewshot.md"
```

## Key Patterns from Dataset

All system prompts enforce these patterns discovered from dataset analysis:

### Text Handling
- **Always quote text**: "SALE 50% OFF"
- **Preserve exact capitalization**: "LPN" not "lpn"
- **Never translate**: Keep original language

### Positioning
- **Grid system**: top-left, center, bottom-right
- **Percentages**: "20% from left"
- **Pixels**: "100px width"

### Colors
- **Name + hex**: "red (#FF0000)"
- **Standard web colors**: Use common names
- **Opacity**: Specify percentages

### Sizes
- **Relative**: "15% of image width"
- **Absolute**: "48px font size"
- **Proportional**: "2x larger than original"

## Migration Path

### From Old Style to New

**Old (Mixed Guide + Prompt):**
```markdown
# Template Title
This template helps you understand...
Background information...
## How to use
[Long explanation]
```

**New System Prompt:**
```markdown
---
output_type: single_string
description: "Brief purpose"
model_requirements: "vision_capable"
---
# Instructions
Direct instructions to transform input.
## Rules
[Concise rules]
## Examples
[Input/Output pairs]
# Output ONLY the result.
```

## Performance Comparison

| Template Type | Token Count | Speed | Consistency |
|--------------|-------------|-------|-------------|
| Simple rewriter | ~200 | Fast | High |
| Dataset-grounded | ~400 | Fast | Very High |
| Few-shot extensive | ~800 | Medium | High |
| Specialist | ~350 | Fast | High |
| Multi-person | ~300 | Fast | High |

## Integration with ComfyUI

```python
class QwenImageOptimizer:
    TEMPLATES = {
        "simple": "qwen_image_system_rewriter_v2.md",
        "examples": "qwen_image_system_dataset_grounded.md",
        "fewshot": "qwen_image_system_rewriter_fewshot.md",
        "specialist": "qwen_image_system_specialist.md",
        "multi_person": "qwen_image_system_multi_person.md",
        "multi_source": "qwen_image_system_multi_source.md"
    }
    
    def process(self, image, instruction, template_type="simple"):
        template = load_template(self.TEMPLATES[template_type])
        return vlm_process(image, instruction, template)
```

## Best Practices

1. **Use system prompts for VLM** - Not guides
2. **Choose based on complexity** - Simple tasks = simple prompts
3. **Include examples for clarity** - Dataset-grounded for best results
4. **Keep output format strict** - Single line, no explanations
5. **Test with actual VLM** - Verify outputs match expectations

## Summary

- **6 new system prompts** created following dataset patterns
- **14 legacy prompts** still functional but may need updates
- **7 documentation files** for human reference
- **6 bilingual templates** for Chinese/DiffSynth integration

Total: 33 qwen_image templates properly categorized and optimized for use.