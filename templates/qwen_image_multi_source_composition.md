# Qwen-Image Multi-Source Composition Template

Advanced template for merging elements from multiple source images into cohesive compositions while preserving specific features.

## Core Composition Pattern

```
Integrate [ELEMENT_FROM_IMAGE_1] from [IMAGE_1_DESCRIPTION] 
with [ELEMENT_FROM_IMAGE_2] from [IMAGE_2_DESCRIPTION]
in [TARGET_SCENE_SETTING]
while preserving [SPECIFIC_FEATURES_TO_MAINTAIN]
and maintaining [CONSISTENCY_REQUIREMENTS]
```

## System Prompt

```
You are an expert at compositing elements from multiple source images into seamless, coherent scenes. You must:
1. Identify and extract specific elements from each source image
2. Preserve designated features exactly (faces, expressions, specific attributes)
3. Adapt other elements to fit the new context
4. Ensure natural integration with consistent lighting, perspective, and style
5. Maintain the artistic coherence of the final composition
```

## Multi-Image Analysis Framework

### Step 1: Source Image Decomposition

**Image 1 Analysis:**
```
Primary Element: [subject/object to extract]
Preserve Exactly:
- Facial features: [if applicable]
- Expression: [specific emotion/look]
- Unique attributes: [distinctive features]
Adaptable Elements:
- Clothing: [can be changed]
- Pose: [can be adjusted]
- Scale: [can be resized]
```

**Image 2 Analysis:**
```
Secondary Element: [what to take from this image]
Extract:
- Style attributes: [design elements]
- Environmental context: [setting details]
- Color palette: [if relevant]
Transfer Properties:
- Material/texture: [surface qualities]
- Lighting style: [illumination characteristics]
```

### Step 2: Integration Strategy

```
Composition Plan:
1. Base Scene: [primary environment/setting]
2. Subject Placement: [where main element goes]
3. Feature Preservation: [what must remain unchanged]
4. Style Application: [how secondary elements are applied]
5. Blending Method: [how to merge naturally]
```

## Common Composition Patterns

### Pattern 1: Character + Outfit/Style Swap

**Template:**
```
Take [PERSON] from image 1, preserving their exact face and expression,
dress them in [OUTFIT/ARMOR/COSTUME] from image 2,
place in [ENVIRONMENT] from image 3,
maintaining original facial features, skin tone, and expression perfectly
```

**Example:**
```
Integrate the young woman from picture one preserving her exact face,
wearing the futuristic cybernetic fox suit from picture two,
standing in the sunny forest from picture three,
maintaining her original facial features and expression unchanged
```

### Pattern 2: Face Preservation with Context Change

**Template:**
```
Extract [SUBJECT]'s face from source image,
apply to [BODY/FIGURE] in different outfit/pose,
set in [NEW_ENVIRONMENT],
ensure perfect facial match including skin tone, features, and expression
```

**Example:**
```
Use the woman's face from the portrait photo,
place on a body wearing cyberpunk armor,
position in neon-lit city street,
preserving exact facial features and natural skin tone
```

### Pattern 3: Multi-Element Scene Assembly

**Template:**
```
Combine:
- [ELEMENT_A] from image 1 (specify preservation needs)
- [ELEMENT_B] from image 2 (specify adaptation allowed)
- [ELEMENT_C] from image 3 (specify role in composition)
In unified scene with [LIGHTING/STYLE] consistency
```

**Example:**
```
Combine:
- Woman's face and upper body from image 1 (preserve face exactly)
- Futuristic weapon and armor design from image 2 (adapt to body proportions)
- Forest background and lighting from image 3 (use as environment)
Creating cohesive scene with consistent sunlight direction
```

## Preservation Specifications

### Facial Feature Lock

**Critical Preservation:**
```
MUST PRESERVE from source:
- Exact eye shape, color, and expression
- Precise nose structure and proportions
- Exact mouth shape and expression
- Original skin tone and texture
- Facial bone structure and proportions
- Any unique features (moles, freckles, etc.)
```

### Expression Transfer

**Emotion Preservation:**
```
Maintain from original:
- Eye expression (gaze direction, openness)
- Mouth position (smile, neutral, etc.)
- Overall facial emotion
- Muscle tension patterns
- Natural asymmetries
```

## Advanced Composition Techniques

### 1. Layer-Based Integration

```
Background Layer: [ENVIRONMENT from image X]
Mid-ground Layer: [SECONDARY ELEMENTS from image Y]
Foreground Layer: [MAIN SUBJECT from image Z]
Overlay Effects: [ATMOSPHERIC ELEMENTS from image W]

Integration order:
1. Establish base environment
2. Place main subject with preserved features
3. Add secondary elements with proper occlusion
4. Apply atmospheric effects for cohesion
```

### 2. Style Transfer with Feature Lock

```
Source Subject: [PERSON from image 1]
Style Reference: [ARTISTIC STYLE from image 2]
Preservation Mask: [FACE remains photorealistic]

Application:
- Apply style to clothing and body
- Preserve photorealistic face
- Blend transition zones smoothly
- Match overall color grading
```

### 3. Semantic Element Swapping

```
Original: [DESCRIPTION of source image]
Swap Map:
- Head/Face → Preserve from Image A
- Outfit → Replace with Image B design
- Pose → Adapt from Image C
- Environment → Use Image D setting
- Lighting → Match Image D ambiance
```

## Complex Integration Examples

### Example 1: Sci-Fi Character Creation
```
Integrate:
A stylized illustration of a young woman from picture one in a sunny forest,
preserving her face. She should be wearing the futuristic cybernetic suit 
with fox-like features from picture two, holding the weapon from picture three,
rendered in a sleek, modern design while preserving her exact facial features 
and expression. The forest setting should maintain the original warm lighting 
and perspective.
```

### Example 2: Fashion Composite
```
Merge:
The model's face and hairstyle from the headshot photo (image 1),
with the elegant dress design from the fashion sketch (image 2),
posed like the dancer in image 3,
in the grand ballroom setting from image 4,
maintaining photorealistic face while stylizing the dress artistically
```

### Example 3: Fantasy Character Assembly
```
Combine:
The warrior's face from the portrait (preserve exactly),
with dragon-scale armor from concept art (adapt to body),
wielding the magical staff from game artwork (adjust scale),
standing in the mystical forest from landscape photo,
with glowing effects from reference image applied as overlay
```

## Technical Specifications

### Input Handling

```yaml
image_sources:
  primary_subject:
    source: image_1
    extract: face, expression
    preserve: 100%
  
  style_element:
    source: image_2
    extract: outfit, design
    adapt: fit to subject
  
  environment:
    source: image_3
    extract: background, lighting
    modify: as needed

composition_rules:
  - preserve_priority: facial_features
  - adapt_priority: clothing, pose
  - blend_priority: edges, transitions
```

### Merge Instructions Syntax

**Explicit Preservation:**
```
"from picture one" + "preserving her face/features/expression"
```

**Element Transfer:**
```
"wearing the [ITEM] from picture two"
"in the [SETTING] from picture three"
"with the [STYLE] of image four"
```

**Consistency Requirements:**
```
"maintaining original [lighting/perspective/mood]"
"matching the [style/tone/atmosphere]"
"ensuring natural integration"
```

## Quality Assurance Checklist

### Pre-Composition Verification
- [ ] All source images identified and numbered
- [ ] Preservation requirements explicitly stated
- [ ] Adaptation allowances clearly defined
- [ ] Target environment/style specified

### Feature Preservation Check
- [ ] Facial features match source exactly
- [ ] Expression maintained accurately
- [ ] Skin tone preserved correctly
- [ ] Unique identifiers retained

### Integration Quality
- [ ] Lighting consistency across elements
- [ ] Perspective alignment correct
- [ ] Scale relationships natural
- [ ] Edge blending seamless
- [ ] Style coherence maintained

### Final Validation
- [ ] Preserved elements unchanged
- [ ] Adapted elements fit naturally
- [ ] Overall composition balanced
- [ ] No uncanny valley effects
- [ ] Artistic intent achieved

## Common Issues and Solutions

### Issue: Face looks different
**Solution:** Use explicit preservation language:
```
"preserving exact facial features, expression, and skin tone from source"
```

### Issue: Elements don't blend naturally
**Solution:** Specify integration method:
```
"with natural lighting transitions and edge blending"
```

### Issue: Style inconsistency
**Solution:** Define unified approach:
```
"maintain consistent artistic style throughout composition"
```

### Issue: Wrong element extracted
**Solution:** Use specific identifiers:
```
"the woman in red dress from first image, not the background figure"
```

## Prompt Construction Formula

```
[ACTION: Integrate/Combine/Merge]
[ELEMENT_1] from [SOURCE_1] with [PRESERVATION_SPEC],
[ELEMENT_2] from [SOURCE_2] with [ADAPTATION_SPEC],
in [ENVIRONMENT] from [SOURCE_3],
[STYLE_MODIFIER],
while [CONSISTENCY_REQUIREMENTS],
ensuring [QUALITY_SPECIFICATIONS]
```

This template enables precise multi-image composition while maintaining critical feature preservation and natural integration.