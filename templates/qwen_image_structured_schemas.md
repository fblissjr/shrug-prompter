# Qwen-Image Structured Schema Templates

Structured attribute-based schemas for precise image editing with qwen-image model.

## Basic Schema Format

```yaml
task_type: [add|remove|replace|modify|transform]
target: [specific element]
attributes:
  property1: value1
  property2: value2
context:
  preserve: [list of unchanged elements]
  blend: [integration method]
```

## Text Operation Schemas

### Add Text Schema
```yaml
operation: add_text
text:
  content: "Your Text Here"
  language: english
  case: uppercase
position:
  horizontal: center  # left|center|right
  vertical: top       # top|center|bottom
  offset_x: 0px
  offset_y: 20px
style:
  font_family: Arial
  font_size: 24px
  font_weight: bold   # normal|bold|light
  font_style: normal  # normal|italic
  color: #FFFFFF
  outline: 
    color: #000000
    width: 2px
  shadow:
    x: 2px
    y: 2px
    blur: 4px
    color: rgba(0,0,0,0.5)
background:
  type: none  # none|solid|gradient
  color: transparent
  padding: 10px
```

### Replace Text Schema
```yaml
operation: replace_text
target:
  current_text: "OLD TEXT"
  location: auto_detect  # auto_detect|specific_position
replacement:
  new_text: "NEW TEXT"
  maintain_style: true
  maintain_position: true
  maintain_size: true
adjustments:
  scale_to_fit: true
  word_wrap: false
```

## Object Operation Schemas

### Add Object Schema
```yaml
operation: add_object
object:
  type: person
  description: "young woman with brown hair"
  pose: standing
  expression: smiling
  clothing: "red dress"
position:
  placement: foreground  # foreground|midground|background
  coordinates:
    x: center
    y: bottom
  scale: 0.3  # relative to image
  rotation: 0deg
integration:
  lighting: match_scene
  shadows: auto_generate
  perspective: auto_adjust
  occlusion: respect_layers
```

### Remove Object Schema
```yaml
operation: remove_object
target:
  description: "person in blue shirt"
  location: left_side
  selection_mode: automatic  # automatic|bbox|mask
removal:
  method: content_aware  # content_aware|blur|crop
  fill: auto_generate    # auto_generate|extend_background
cleanup:
  smooth_edges: true
  blend_radius: 5px
```

### Replace Object Schema
```yaml
operation: replace_object
source:
  identify: "red car"
  location: center
destination:
  object: "blue motorcycle"
  attributes:
    color: metallic_blue
    style: sport
    size: similar_to_source
matching:
  position: maintain
  scale: maintain
  orientation: maintain
  lighting: adapt
  shadows: regenerate
```

## Style Transformation Schemas

### Color Adjustment Schema
```yaml
operation: color_adjustment
targets:
  - element: background
    adjustments:
      hue: +30deg
      saturation: +20%
      brightness: -10%
      contrast: +15%
  - element: foreground_object
    adjustments:
      color_map:
        from: "#FF0000"
        to: "#0000FF"
preserve:
  - text_elements
  - skin_tones
  - brand_colors
```

### Style Transfer Schema
```yaml
operation: style_transfer
style:
  name: oil_painting
  reference: "van_gogh_starry_night"
  intensity: 0.7  # 0.0 to 1.0
parameters:
  brush_size: medium
  texture_detail: high
  color_palette: vibrant
  stroke_direction: swirls
content_preservation:
  subjects: high
  edges: medium
  details: low
```

### Lighting Change Schema
```yaml
operation: lighting_adjustment
lighting:
  type: golden_hour
  direction: west
  intensity: warm
  time_of_day: sunset
adjustments:
  shadows:
    length: long
    softness: medium
    opacity: 0.6
  highlights:
    intensity: bright
    color: "#FFD700"
  ambient:
    level: medium
    tint: orange
atmosphere:
  add_sun_rays: true
  add_lens_flare: false
  atmospheric_haze: light
```

## Complex Composition Schemas

### Multi-Element Edit Schema
```yaml
operation: composite_edit
edits:
  - step: 1
    action: remove
    target: "background clutter"
  - step: 2
    action: add
    element: "clean white background"
  - step: 3
    action: add
    element: "company logo"
    position: top_right
  - step: 4
    action: adjust
    property: brightness
    value: +15%
validation:
  check_order: sequential
  rollback_on_error: true
```

### Layout Reorganization Schema
```yaml
operation: layout_reorganization
current_layout:
  scan: automatic
  identify_elements: true
new_layout:
  arrangement: grid  # grid|centered|asymmetric|golden_ratio
  spacing: 20px
  alignment: center
  distribution: even
elements:
  - id: main_subject
    position: center
    scale: 1.0
  - id: text_block
    position: bottom
    scale: 0.8
  - id: logo
    position: top_right
    scale: 0.15
```

## Special Effects Schemas

### Shadow/Reflection Schema
```yaml
operation: add_shadow
target: 
  element: "floating object"
  auto_detect: true
shadow:
  type: drop_shadow  # drop_shadow|cast_shadow|contact_shadow
  direction: 
    angle: 45deg
    distance: 30px
  properties:
    blur: 15px
    opacity: 0.5
    color: "#000000"
    scale: 1.0
  surface:
    type: ground_plane
    perspective: true
```

### Blur Effect Schema
```yaml
operation: selective_blur
focus:
  subject: "person in center"
  sharpness: maximum
blur:
  type: gaussian  # gaussian|motion|radial|tilt_shift
  intensity: 
    near: 0%
    far: 80%
  gradient:
    type: depth_based
    falloff: smooth
exclude:
  - text_elements
  - faces
```

## Batch Processing Schema

```yaml
batch_operation:
  input:
    source: folder_path
    count: 50
    format: jpg
  
  process:
    - operation: resize
      dimensions:
        width: 1080
        height: 1080
        maintain_aspect: true
        fill: white
    
    - operation: add_watermark
      watermark:
        type: logo
        file: company_logo.png
        position: bottom_right
        size: 10%
        opacity: 70%
    
    - operation: color_correct
      auto_balance: true
      enhance_contrast: true
  
  output:
    destination: output_folder
    format: jpg
    quality: 95
    naming: "{original_name}_edited"
```

## Conditional Logic Schema

```yaml
operation: conditional_edit
conditions:
  - if:
      image_brightness: dark  # < 30%
    then:
      action: increase_exposure
      value: +30%
  
  - if:
      has_text: true
      text_color: light
    then:
      action: add_background
      type: dark_overlay
      opacity: 50%
  
  - if:
      aspect_ratio: portrait
    then:
      action: add_border
      sides: [left, right]
      color: white
      width: 100px
```

## Quality Control Schema

```yaml
operation: quality_enhancement
analysis:
  check_resolution: true
  check_sharpness: true
  check_noise: true
  check_exposure: true

improvements:
  upscale:
    enable: true
    target_resolution: 4K
    method: AI_enhanced
  
  denoise:
    enable: true
    strength: medium
    preserve_details: true
  
  sharpen:
    enable: true
    amount: 30%
    radius: 1.0px
    threshold: 0
  
  color:
    auto_correct: true
    vibrance: +10%
    fix_white_balance: true

validation:
  min_quality_score: 85
  require_faces_intact: true
  require_text_readable: true
```

## Accessibility Schema

```yaml
operation: accessibility_enhancement
requirements:
  wcag_level: AAA
  
text_adjustments:
  minimum_size: 16px
  contrast_ratio: 7.0
  add_outline: true
  background_padding: 5px

color_adjustments:
  ensure_distinguishable: true
  avoid_color_only_info: true
  
alt_versions:
  high_contrast:
    create: true
    foreground: "#000000"
    background: "#FFFFFF"
  
  dark_mode:
    create: true
    invert_colors: selective
    preserve_images: true
```

## Animation Frame Schema

```yaml
operation: animation_frame
frame_info:
  number: 5
  total: 30
  fps: 24

motion:
  object: "ball"
  start_position:
    x: 100px
    y: 200px
  end_position:
    x: 500px
    y: 200px
  interpolation: ease_in_out
  
motion_effects:
  motion_blur:
    enable: true
    strength: medium
    direction: horizontal
  
  squash_stretch:
    enable: true
    amount: 10%
    
timing:
  keyframe: false
  tween: true
```

## Metadata Schema

```yaml
operation: edit_with_metadata
edit_tracking:
  version: 1.2
  timestamp: 2024-01-15T10:30:00Z
  author: system
  
modifications:
  - type: add_text
    description: "Added sale badge"
    revertable: true
    
preservation:
  original_backup: true
  exif_data: maintain
  color_profile: sRGB
  
output:
  format: png
  compression: lossless
  dimensions: original
  dpi: 300
```

## Usage Notes

1. **Schema Flexibility**: Mix and match attributes as needed
2. **Default Values**: Unspecified attributes use sensible defaults
3. **Validation**: Schema validates before processing
4. **Error Handling**: Graceful fallbacks for invalid values
5. **Extensibility**: Add custom attributes as needed

These schemas provide structured, precise control over image editing operations while maintaining clarity and consistency.