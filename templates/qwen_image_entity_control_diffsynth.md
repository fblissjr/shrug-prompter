# Qwen-Image Entity Control Template (DiffSynth Official)
# Source: examples/qwen_image/model_inference/Qwen-Image-EliGen.py

## Overview
Entity Control (EliGen) allows precise control over specific elements in the generated image through entity prompts and masks.

## System Prompt
You are creating prompts for Qwen-Image with Entity Control, which allows precise placement and description of specific elements within the overall scene.

## Structure

### Global Prompt
The overall scene description that sets the context for all entities.

### Entity Prompts
Individual descriptions for specific elements that will be controlled independently.

## Example Entity Control Setup

### Simple Example
```python
global_prompt = "A beautiful girl wearing shirt and shorts in the street, holding a sign 'Entity Control'"

entity_prompts = [
    "girl",           # Entity 1: Main subject
    "shirt",          # Entity 2: Clothing item
    "shorts",         # Entity 3: Clothing item  
    "sign",           # Entity 4: Held object
    "street"          # Entity 5: Background
]
```

### Complex Example
```python
global_prompt = "A breathtaking beauty of Raja Ampat by the late-night moonlight, one beautiful woman from behind wearing a pale blue long dress with soft glow, sitting at the top of a cliff looking towards the beach, pastell light colors, a group of small distant birds flying in far sky, a boat sailing on the sea, best quality, realistic"

entity_prompts = [
    "beautiful woman from behind",      # Entity 1: Main subject
    "pale blue long dress with glow",   # Entity 2: Clothing
    "cliff top",                        # Entity 3: Foreground location
    "beach below",                       # Entity 4: Background location
    "group of distant birds",           # Entity 5: Sky element
    "boat on the sea",                  # Entity 6: Sea element
    "late-night moonlight"              # Entity 7: Lighting
]
```

## Entity Prompt Guidelines

### Entity Types
1. **Main Subject**: Person, animal, or primary object
2. **Clothing/Accessories**: Specific garments or items worn/held
3. **Environmental Elements**: Ground, sky, buildings, nature
4. **Props/Objects**: Items in the scene
5. **Lighting/Effects**: Light sources, atmospheric effects

### Entity Description Patterns

#### Minimal (Single Word)
- "girl"
- "sword"
- "tree"

#### Descriptive (With Attributes)
- "beautiful woman from behind"
- "pale blue flowing dress"
- "glowing red sword"

#### Detailed (With Context)
- "samurai girl in traditional kimono"
- "ancient palace on misty mountain"
- "group of birds flying in formation"

## Mask Association
Each entity prompt corresponds to a mask region where that element should appear:
- Mask areas define where entities can be generated
- Overlapping masks allow interaction between entities
- Empty mask areas follow global prompt

## Best Practices

### Global Prompt
1. **Comprehensive Scene**: Include all elements in natural language
2. **Maintain Flow**: Write as cohesive description, not list
3. **Include Quality Tags**: Add style and quality modifiers at end
4. **Set Atmosphere**: Establish mood and lighting

### Entity Prompts
1. **Be Specific**: Clear, unambiguous descriptions
2. **Hierarchical**: Order from most to least important
3. **Avoid Redundancy**: Don't repeat global prompt details
4. **Consistent Style**: Match tone with global prompt

## Advanced Entity Control

### Spatial Relationships
```python
entity_prompts = [
    "woman sitting",           # Position: seated
    "cliff edge",              # Location: edge
    "beach far below",         # Distance: far
    "birds in distant sky",    # Height: sky level
    "moon overhead"            # Position: above
]
```

### Interaction Between Entities
```python
entity_prompts = [
    "girl holding sword",      # Subject with object
    "bird on her hand",        # Object on subject
    "dress flowing in wind",   # Clothing affected by environment
    "reflection in water"      # Environmental interaction
]
```

### Text in Images
```python
global_prompt = "A beautiful girl holding a sign with text"
entity_prompts = [
    "girl",
    "sign with 'Entity Control' text"  # Specific text content
]
```

## Prompt Formula for Entity Control

### Global
`[Scene description] + [All elements in natural flow] + [Atmosphere] + [Quality tags]`

### Entities
`[Entity type] + [Key attributes] + [Distinguishing features]`

## Common Entity Combinations

### Portrait Scene
- Entity 1: "person/face"
- Entity 2: "clothing/outfit"
- Entity 3: "background environment"
- Entity 4: "lighting/atmosphere"

### Landscape with Figure
- Entity 1: "landscape/environment"
- Entity 2: "figure/person"
- Entity 3: "foreground elements"
- Entity 4: "sky/atmosphere"
- Entity 5: "additional objects"

## Usage Notes
- Entity Control requires masks for each entity
- Masks can be generated automatically or provided manually
- Entity prompts should be shorter than global prompt
- Test with simple entities before complex compositions
- Order matters: earlier entities have priority