# Qwen-Image Edit Structured Template

## System Prompt Format

The model uses these system prompts (tokenizer markers handled automatically):

### Descriptive System Prompt
```
Describe the image by detailing the color, shape, size, texture, quantity, text, spatial relationships of the objects and background:
```

### Edit Instruction System Prompt
```
Describe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input
```

## Structured Edit Instruction Template

Based on the qwen-image dataset patterns, here's the optimal structure for edit instructions:

### Primary Template Structure

```
Image Analysis:
- Objects: [List main objects with positions]
- Text: [Any text content in quotes with location]
- Colors: [Dominant colors and their distribution]
- Background: [Background description]
- Style: [Overall visual style]

Edit Instruction:
[TASK_TYPE] [TARGET_SPECIFICATION] [MODIFICATION_DETAILS] [PRESERVATION_REQUIREMENTS]

Expected Output:
- Primary Change: [What will be modified]
- Preserved Elements: [What remains unchanged]
- Consistency Check: [How it maintains scene coherence]
```

## Task-Specific Templates

### 1. Text Addition/Modification

**User Instruction:**
```
Add text "[TEXT_CONTENT]" in [COLOR] [FONT_STYLE] at [POSITION], [SIZE]px, maintaining [BACKGROUND/LAYOUT]
```

**Expected Response:**
```
The image contains [describe current elements]. Adding "[TEXT_CONTENT]" text element:
- Position: [POSITION] of the composition
- Style: [FONT_STYLE] typeface in [COLOR]
- Size: [SIZE]px height
- Integration: Overlaid while preserving [PRESERVED_ELEMENTS]
```

### 2. Object Replacement

**User Instruction:**
```
Replace [ORIGINAL_OBJECT] with [NEW_OBJECT] having [ATTRIBUTES], maintain [SCENE_CONTEXT]
```

**Expected Response:**
```
Original: [ORIGINAL_OBJECT] located at [POSITION] with [ORIGINAL_ATTRIBUTES]
Replacement: [NEW_OBJECT] with:
- Attributes: [COLOR, SIZE, TEXTURE, STYLE]
- Position: Same as original [POSITION]
- Integration: Matching [LIGHTING/SHADOW/PERSPECTIVE] of scene
Preserved: [BACKGROUND, OTHER_OBJECTS, COMPOSITION]
```

### 3. Background Transformation

**User Instruction:**
```
Change background to [NEW_BACKGROUND], keep [FOREGROUND_ELEMENTS] unchanged
```

**Expected Response:**
```
Current background: [DESCRIBE_CURRENT]
New background: [NEW_BACKGROUND_DESCRIPTION]
- Style: [STYLE_ATTRIBUTES]
- Colors: [COLOR_PALETTE]
- Mood: [ATMOSPHERE_CHANGE]
Preserved foreground:
- Objects: [LIST_PRESERVED_OBJECTS]
- Positions: Unchanged
- Lighting: Adjusted to match new background
```

### 4. Style Transfer

**User Instruction:**
```
Transform style to [TARGET_STYLE] while preserving [CONTENT_ELEMENTS]
```

**Expected Response:**
```
Original style: [CURRENT_STYLE_DESCRIPTION]
Target transformation:
- Style: [TARGET_STYLE] characteristics
- Color mapping: [ORIGINAL_COLORS] → [NEW_COLORS]
- Texture changes: [TEXTURE_MODIFICATIONS]
- Artistic elements: [STYLE_SPECIFIC_FEATURES]
Content preservation:
- Objects: [MAINTAINED_OBJECTS]
- Composition: [LAYOUT_PRESERVATION]
- Semantic meaning: [UNCHANGED_MEANING]
```

### 5. Complex Multi-Edit

**User Instruction:**
```
1. [FIRST_EDIT]
2. [SECOND_EDIT]
3. [THIRD_EDIT]
```

**Expected Response:**
```
Sequential modifications:

Step 1: [FIRST_EDIT_DESCRIPTION]
- Change: [WHAT_CHANGES]
- Result: [INTERMEDIATE_STATE]

Step 2: [SECOND_EDIT_DESCRIPTION]
- Change: [WHAT_CHANGES]
- Result: [INTERMEDIATE_STATE]

Step 3: [THIRD_EDIT_DESCRIPTION]
- Change: [WHAT_CHANGES]
- Final result: [FINAL_STATE]

Overall consistency maintained through:
- [CONSISTENCY_ELEMENT_1]
- [CONSISTENCY_ELEMENT_2]
```

## Best Practices for Qwen-Image

### 1. Precision Hierarchy
```
Most Precise → Least Precise
━━━━━━━━━━━━━━━━━━━━━━━━━━
Pixel coordinates → Quadrant positions → Relative positions → General areas
Hex colors → Named colors → Color families → Vague descriptors
Exact dimensions → Percentages → Relative sizes → Qualitative sizes
```

### 2. Instruction Complexity Guidelines

**Simple Edit (1 change)**
- Length: 10-20 words
- Format: [VERB] [OBJECT] [ATTRIBUTE] [POSITION]
- Example: "Add red circle, 50px diameter, at center"

**Moderate Edit (2-3 changes)**
- Length: 20-35 words
- Format: [PRIMARY_CHANGE] and [SECONDARY_CHANGE], maintaining [CONTEXT]
- Example: "Replace blue background with sunset gradient, add lens flare at top-left, preserve all text elements"

**Complex Edit (4+ changes)**
- Length: 35-50 words max
- Format: Sequential steps with dependencies
- Example: "First remove background clutter, then add wooden texture, place logo at top-center 100px wide, finally adjust lighting to warm tone"

### 3. Common Patterns from Dataset

**Text Pattern:**
```
"Add text \"[CONTENT]\" in [COLOR] at [POSITION]"
```

**Object Pattern:**
```
"Add [ADJECTIVE] [OBJECT] in [POSITION], [SIZE], facing [DIRECTION]"
```

**Replacement Pattern:**
```
"Replace [OLD] with [NEW] maintaining [PRESERVED_ATTRIBUTES]"
```

**Style Pattern:**
```
"Apply [STYLE] effect with [INTENSITY], preserve [ELEMENTS]"
```

## Validation Checklist

Before finalizing instruction:
- [ ] Text in quotes if applicable
- [ ] Position specified (quadrant/coordinates)
- [ ] Size defined (pixels/percentage/relative)
- [ ] Color specified (name/hex/description)
- [ ] Preservation context stated
- [ ] No conflicting requirements
- [ ] Under 50 words total
- [ ] Follows qwen format markers

## Error Handling

If instruction is ambiguous, use these defaults:
- Position: center
- Size: medium/proportional to image
- Color: neutral/matching existing palette
- Style: consistent with original
- Preservation: all unmentioned elements