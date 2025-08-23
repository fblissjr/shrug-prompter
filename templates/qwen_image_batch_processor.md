# Qwen-Image Batch Edit Processor

Optimized template for processing multiple images with consistent edit instructions using qwen-image model.

## Batch Processing Format

```
System: You are processing image edits. For each image, describe its current state then apply the specified modification consistently.

User: Apply this edit to all images: {batch_instruction}
```

## Batch Instruction Patterns

### Pattern 1: Uniform Text Addition
```
For each image:
1. Identify optimal text placement area
2. Add text "{TEXT}" in {COLOR} {STYLE}
3. Ensure readability against background
4. Maintain consistent size ratio across images
```

### Pattern 2: Consistent Style Application
```
For each image:
1. Preserve core content and composition
2. Apply {STYLE} transformation
3. Adjust intensity based on original brightness
4. Maintain relative color relationships
```

### Pattern 3: Standardized Object Addition
```
For each image:
1. Detect available space for object placement
2. Add {OBJECT} scaled to {SIZE}% of image dimension
3. Match lighting/shadow to scene
4. Avoid occlusion of key elements
```

## Adaptive Edit Rules

### Context-Aware Positioning
```python
if image.has_text_at_top:
    position = "bottom"
elif image.has_clear_center:
    position = "center"
else:
    position = "find_least_busy_area"
```

### Dynamic Sizing
```python
if image.resolution > 2048:
    text_size = "48px"
elif image.resolution > 1024:
    text_size = "36px"
else:
    text_size = "24px"
```

### Smart Color Selection
```python
if background.is_dark:
    text_color = "white or bright"
elif background.is_light:
    text_color = "black or dark"
else:
    text_color = "contrasting_color"
```

## Batch Templates by Use Case

### 1. E-commerce Product Enhancement
```
System: Process product images for e-commerce listing optimization

User: Add "SALE 30% OFF" badge to top-right corner, red background with white text

Expected Edit:
- Position: Top-right corner with 10px margin
- Badge: Rounded rectangle, red (#FF0000) background
- Text: "SALE 30% OFF" in bold white, centered
- Size: 15% of image width
- Shadow: Subtle drop shadow for visibility
```

### 2. Social Media Branding
```
System: Apply consistent branding to social media image batch

User: Add @username watermark and brand colors

Expected Edit:
- Watermark: "@username" at bottom-right, 30% opacity
- Color overlay: Brand blue (#1DA1F2) gradient at top
- Logo: Small brand icon at bottom-left
- Consistency: Same positioning across all images
```

### 3. Document Processing
```
System: Standardize document images for archival

User: Add page numbers and timestamp

Expected Edit:
- Header: "Page [X] of [Y]" at top-center
- Footer: "Archived: [DATE]" at bottom-center
- Font: Arial 10pt black on white background bar
- Margins: 20px padding from edges
```

### 4. Real Estate Listings
```
System: Enhance property photos with listing information

User: Add property details overlay

Expected Edit:
- Top banner: Property address in white on semi-transparent black
- Bottom banner: "3 Bed | 2 Bath | 1,500 sqft" 
- Corner badge: "$450,000" in gold accent
- MLS number: Small text at bottom-right
```

## Batch Consistency Rules

### Maintain Across Batch:
1. **Positioning**: Same relative position in all images
2. **Sizing**: Proportional to image dimensions
3. **Styling**: Identical fonts, colors, effects
4. **Quality**: Consistent resolution and clarity

### Adapt Per Image:
1. **Contrast**: Adjust for visibility on varying backgrounds
2. **Placement**: Shift to avoid covering important content
3. **Scale**: Resize based on image resolution
4. **Rotation**: Match image orientation

## Quality Control Checklist

For each image in batch:
- [ ] Edit applied successfully
- [ ] Text/objects clearly visible
- [ ] No important content obscured
- [ ] Consistent with batch style
- [ ] Proper contrast maintained
- [ ] Resolution preserved
- [ ] File format unchanged

## Optimization Tips

### Processing Efficiency:
1. Group similar images together
2. Use template-based instructions
3. Define clear fallback rules
4. Set standard dimensions upfront

### Common Batch Sizes:
- Small batch: 1-10 images (detailed edits)
- Medium batch: 11-50 images (standard edits)
- Large batch: 51-100 images (simple edits)
- Bulk batch: 100+ images (basic overlays)

## Error Recovery Patterns

### If edit fails on specific image:
```
Fallback sequence:
1. Try alternative position
2. Adjust size/scale
3. Modify color for visibility
4. Skip if incompatible
5. Log for manual review
```

### Validation Loop:
```
for each edited_image:
    if not meets_criteria:
        reprocess with adjusted_parameters
    if still_fails:
        mark for manual_intervention
```

## Batch Command Examples

### Simple Batch:
```
"Add 'Copyright 2024' to all images at bottom-center"
```

### Complex Batch:
```
"For each image: Add title from filename at top, add sequential number at bottom-right, apply subtle vignette, ensure text contrasts with background"
```

### Conditional Batch:
```
"If portrait orientation: add text vertically on right side; If landscape: add text horizontally at bottom"
```

## Performance Metrics

Track for batch optimization:
- Average processing time per image
- Success rate percentage
- Consistency score (0-100)
- Manual intervention rate
- Quality degradation factor