# Qwen-Image Simple Prompt Templates

Clean, efficient prompts for qwen-image edit model. The tokenizer markers (im_start/im_end) are handled automatically by the model.

## Core System Prompts

### Descriptive Analysis
```
Describe the image by detailing the color, shape, size, texture, quantity, text, spatial relationships of the objects and background:
```

### Edit Instruction
```
Describe the key features of the input image, then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input
```

## Quick Edit Templates

### 1. Text Operations

**Add Text:**
```
Add text "[CONTENT]" in [COLOR] at [POSITION]
```

**Replace Text:**
```
Replace "[OLD_TEXT]" with "[NEW_TEXT]"
```

**Remove Text:**
```
Remove all text from [LOCATION]
```

### 2. Object Operations

**Add Object:**
```
Add [OBJECT] with [COLOR/SIZE] at [POSITION]
```

**Replace Object:**
```
Replace [OLD_OBJECT] with [NEW_OBJECT]
```

**Remove Object:**
```
Remove [OBJECT] from [POSITION]
```

### 3. Style Operations

**Color Change:**
```
Change [TARGET] color to [NEW_COLOR]
```

**Background Change:**
```
Replace background with [NEW_BACKGROUND]
```

**Style Transfer:**
```
Apply [STYLE_NAME] style to entire image
```

## Precision Templates

### Spatial Positioning
```
top-left | top-center | top-right
left     | center     | right
bottom-left | bottom-center | bottom-right
```

### Size Specifications
```
Small: 10-20% of image
Medium: 30-40% of image
Large: 50-60% of image
```

### Color Specifications
```
Primary: red, blue, yellow
Secondary: green, orange, purple
Neutral: black, white, gray
```

## Common Use Cases

### E-commerce
```
Add "SALE" badge in red at top-right corner
Add price "$99.99" in white at bottom-left
Remove background, replace with white
```

### Social Media
```
Add "@username" watermark at bottom-right
Add emoji 😍 at top-left corner
Apply vintage filter effect
```

### Document
```
Add page number at bottom-center
Add header "CONFIDENTIAL" in red at top
Highlight text in yellow
```

### Photo Editing
```
Remove person from left side
Replace sky with sunset
Add lens flare at top-right
```

## Composite Instructions

### Two-Step Edit
```
Remove background and add white background
```

### Three-Step Edit
```
Add title at top, add border, change background color
```

### Complex Edit
```
Replace all blue with green, add logo at corner, increase brightness
```

## Batch Processing

### Uniform Application
```
Apply to all: Add watermark at bottom-right
```

### Conditional Application
```
If dark image: Add white text; If light image: Add black text
```

## Best Practices

### DO:
- Use quotes for text content
- Specify exact positions
- Keep instructions under 50 words
- Preserve original language in text

### DON'T:
- Use vague positions ("somewhere")
- Forget quotation marks for text
- Combine conflicting instructions
- Translate text content

## Quick Reference

### Task Verbs
- Add, Remove, Replace, Change, Modify
- Transform, Apply, Enhance, Adjust, Convert

### Position Terms
- Corner, edge, center, side
- Top, bottom, left, right
- Foreground, background, middle

### Size Terms
- Pixels (px), percentage (%), scale
- Small, medium, large
- Tiny, huge, proportional

### Style Terms
- Modern, vintage, minimalist
- Bold, subtle, dramatic
- Bright, dark, muted

## One-Line Examples

```
Add "NEW" in red at top-left
Remove all people from image
Replace blue sky with cloudy sky
Change shirt color to green
Add sunglasses to face
Remove background completely
Add shadow effect to text
Make image black and white
Crop to square format
Add rainbow in background
```

## Error Handling

If instruction unclear, default to:
- Position: center
- Size: medium
- Color: black text on light, white text on dark
- Style: match existing

## Performance Tips

1. **Fastest**: Single object/text operations
2. **Fast**: Color/style changes
3. **Moderate**: Multiple object edits
4. **Slow**: Complex scene reconstructions

## Validation

Quick check before sending:
1. ✓ Clear action verb
2. ✓ Specific target
3. ✓ Position defined
4. ✓ Text in quotes
5. ✓ Under 50 words