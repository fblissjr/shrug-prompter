# Qwen-Image Multi-Person Composition Guide

Comprehensive guide for combining multiple people from different source images into cohesive compositions.

## Overview

Multi-person composition involves merging individuals from separate images while preserving their unique identities. This is crucial for:
- Group photos from individual portraits
- Social media composites
- Professional team photos
- Creative photo montages

## Key Principles

### 1. Identity Preservation
Each person must maintain their distinct features:
- **Never blend features** between different people
- **Preserve unique characteristics** of each individual
- **Maintain ethnic features** accurately
- **Keep body proportions** individual to each person

### 2. Clear Identification
Always identify people explicitly:
- Person 1 (from first/left image)
- Person 2 (from second/right image)
- Never use vague terms like "both women"

## System Prompt Usage

Use the system prompt template: `qwen_image_system_multi_person.md`

### Basic Structure
```python
system_prompt = load_template("qwen_image_system_multi_person.md")
user_instruction = "Combine these two people at the beach"
```

## Composition Strategies

### Side-by-Side Placement
```
Place Person 1 on the left side and Person 2 on the right side
Position both subjects standing next to each other
Arrange Person 1 and Person 2 side by side
```

### Interactive Positioning
```
Person 1 with arm around Person 2's shoulder
Both people facing camera, Person 1 slightly forward
Person 2 standing behind Person 1
```

### Spatial Relationships
```
Person 1 at 40% from left, Person 2 at 60% from left
Both subjects in foreground, Person 1 closer to camera
Equal spacing with 30cm gap between them
```

## Feature Analysis Checklist

For each person, document:

### Facial Features
- Eye shape and color
- Nose structure
- Mouth shape
- Face shape (oval, round, square)
- Skin tone (with hex code if possible)

### Hair
- Color (specific shade)
- Style (straight, curly, wavy)
- Length (short, medium, long)

### Body Characteristics
- Build (athletic, average, etc.)
- Height indication
- Posture

## Common Scenarios

### Beach Vacation
```
Create beach scene with Person 1 (asian woman from left image) 
wearing blue floral swimsuit and Person 2 (woman from right image) 
wearing coral one-piece, both standing on sandy beach with ocean behind, 
maintaining each person's unique facial features and body type
```

### Business Meeting
```
Place Person 1 from first input in business suit on left side of 
conference table, Person 2 from second input in professional attire 
on right side, both in modern office setting, preserve individual 
appearances completely
```

### Casual Outing
```
Position Person 1 from first image wearing casual outfit at outdoor 
cafe table left seat, Person 2 from second image in their outfit at 
right seat, maintain distinct identities, natural lighting
```

## Technical Specifications

### Input Handling
- **First image**: Primary subject (Person 1)
- **Second image**: Secondary subject (Person 2)
- **Additional images**: Person 3, 4, etc.
- **Reference clearly**: "from first/left image", "from second/right image"

### Composition Rules
1. Scale people proportionally to each other
2. Match lighting direction on all subjects
3. Ensure consistent perspective
4. Harmonize color grading
5. Maintain individual features

### Integration Requirements
- Consistent shadows
- Natural spacing
- Proper depth relationships
- Unified color temperature
- Seamless edge blending

## Troubleshooting

### Problem: Only First Person Appears
**Solution**: Explicitly reference "combine BOTH Person 1 from first image AND Person 2 from second image"

### Problem: Features Get Mixed
**Solution**: Add "maintain completely separate identities, no feature blending"

### Problem: Wrong Person Modified
**Solution**: Use "keep Person 1 exactly as shown in first image, only adjust Person 2's position"

### Problem: Unnatural Scaling
**Solution**: Specify "maintain natural height proportions between Person 1 and Person 2"

## Enhanced Instruction Formats

### Format 1: Detailed Description
```
Combine two people: Person 1 (asian woman, black shoulder-length hair, 
athletic build, from left image) and Person 2 (caucasian woman, blonde 
hair, different build, from right image) in beach scene, both in 
swimwear, standing together, preserve individual identities
```

### Format 2: Positional Focus
```
Place Person 1 from image 1 at left position (30% from left edge) 
and Person 2 from image 2 at right position (70% from left edge) 
on beach background, maintain original appearances
```

### Format 3: Identity Lock
```
Insert both people preserving exact features: Person 1 with their 
specific asian features intact, Person 2 with their specific features 
intact, no mixing of characteristics, beach setting
```

## Quality Validation

Before finalizing, verify:
- ✓ Both people visible and recognizable
- ✓ Individual features preserved
- ✓ No feature mixing between people
- ✓ Natural positioning and scale
- ✓ Consistent lighting on both
- ✓ Appropriate interaction/spacing
- ✓ Background properly integrated

## Best Practices

1. **Always** identify each person explicitly
2. **Never** use vague identifiers
3. **Describe** each person's features separately
4. **Specify** position for each individual
5. **Preserve** unique characteristics
6. **Reference** source images clearly
7. **Maintain** identity separation

## Integration with Other Templates

Can be combined with:
- `qwen_image_system_rewriter.md` for instruction clarity
- `qwen_image_system_multi_source.md` for element mixing
- Style templates for artistic effects

## Example Workflow

```python
# Load system prompt
system_prompt = load_template("qwen_image_system_multi_person.md")

# User provides two portrait images
image1 = "portrait1.jpg"  # Asian woman
image2 = "portrait2.jpg"  # Caucasian woman

# User instruction
instruction = "Put them together at a beach"

# System generates precise instruction
output = """
Combine Person 1 (asian woman with black hair from first image) 
and Person 2 (caucasian woman with blonde hair from second image) 
standing together on sunny beach, Person 1 on left wearing blue 
swimsuit, Person 2 on right wearing red swimsuit, both facing 
camera with ocean background, maintain individual facial features 
and body types exactly as shown in source images
"""
```

This ensures both inputs are recognized and processed as separate individuals with preserved identities.