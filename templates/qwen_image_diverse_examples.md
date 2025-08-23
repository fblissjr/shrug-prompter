# Qwen-Image Diverse Examples with Real Dataset Patterns

Based on actual qwen-image dataset patterns, here are diverse, practical examples for different edit scenarios.

## Text-Based Edits (Most Common in Dataset)

### Example 1: Product Label
```
Original: White coffee mug on wooden table
Edit: Add text "WORLD'S BEST DAD" in black bold letters on the mug center
Result: Mug now displays centered text with proper curve following mug shape
```

### Example 2: Signage Update
```
Original: Blank storefront window
Edit: Add "OPEN 24 HOURS" in neon green glowing text at top-center
Result: Luminous green text with glow effect positioned prominently
```

### Example 3: Multi-Language Text
```
Original: Restaurant menu board
Edit: Replace "Today's Special" with "本日のスペシャル" maintaining font size
Result: Japanese text in same position and style as original English
```

## Object Manipulation Examples

### Example 4: Character Addition
```
Original: Empty park bench under tree
Edit: Add elderly man in blue sweater reading newspaper on left side of bench
Result: Man naturally seated, newspaper held at reading angle, shadows consistent
```

### Example 5: Animal Replacement
```
Original: Golden retriever on grass
Edit: Replace dog with orange tabby cat in same pose
Result: Cat maintains similar posture, grass interaction realistic
```

### Example 6: Technology Update
```
Original: Old CRT monitor on desk
Edit: Replace with modern 27" flat screen displaying same content
Result: Sleek monitor properly scaled, cables and stand updated
```

## Style Transformations

### Example 7: Time of Day
```
Original: Noon cityscape with harsh shadows
Edit: Transform to golden hour lighting with warm orange tones
Result: Sun position lowered, long shadows, warm color grading throughout
```

### Example 8: Weather Change
```
Original: Sunny beach scene
Edit: Add storm clouds and rough waves, maintain foreground umbrella
Result: Dark clouds overhead, whitecaps on waves, umbrella slightly bent from wind
```

### Example 9: Artistic Style
```
Original: Realistic portrait photo
Edit: Apply oil painting style with visible brushstrokes
Result: Painterly texture, color blending, canvas-like appearance
```

## Schema-Based Edit Instructions

### Example 10: E-commerce Enhancement
```
task: add_overlay
elements:
  badge: "NEW ARRIVAL"
  position: top-left
  size: 20% width
  color: #FF6B35
  style: rounded rectangle
  shadow: 2px drop
preserve:
  - product visibility
  - original colors
  - image quality
```

### Example 11: Real Estate Overlay
```
operation: property_info
overlay_elements:
  address: "123 Main St"
  price: "$450,000"
  details: "3BR | 2BA | 1850 sqft"
positioning:
  address: top-banner
  price: bottom-left-badge
  details: bottom-banner
styling:
  background: semi-transparent-black
  text: white-bold
  margins: 10px
```

### Example 12: Social Media Template
```
edit_type: branding
watermark:
  text: "@photographer_jane"
  location: bottom-right
  opacity: 40%
  font: sans-serif
border:
  style: thin-white
  width: 5px
filter:
  type: subtle-vignette
  intensity: 20%
```

## Complex Multi-Step Edits

### Example 13: Event Poster Creation
```
Step 1: Replace background with gradient (purple to blue)
Step 2: Add text "SUMMER FEST 2024" in white at top
Step 3: Add date "July 15-17" in yellow below title
Step 4: Add musical note icons around edges
```

### Example 14: Before/After Split
```
Original: Messy room photo
Edit sequence:
1. Duplicate image side by side
2. Clean/organize right half
3. Add vertical divider line
4. Add "BEFORE" and "AFTER" labels
```

## Regional Edit Examples

### Example 15: Selective Color Change
```
Target: Red car in parking lot
Edit: Change only the car color to metallic blue
Preserve: All other cars, reflections, shadows
```

### Example 16: Background Blur
```
Subject: Person in foreground
Edit: Apply bokeh blur to background only
Depth: Progressive blur based on distance
```

## Batch Processing Examples

### Example 17: Consistent Watermarking
```
Batch of 50 product images:
- Add logo at bottom-right corner
- Size: 10% of image width
- Opacity: 70%
- Maintain aspect ratio
```

### Example 18: Standardized Dimensions
```
Mixed size images:
- Resize all to 1080x1080
- Center content
- Fill margins with white
- Preserve original aspect within frame
```

## Error Recovery Examples

### Example 19: Ambiguous Position Fix
```
Original instruction: "Add text somewhere visible"
Improved: "Add text at top-center with 30px margin, ensuring contrast with background"
```

### Example 20: Conflicting Requirements
```
Original: "Make it bright but keep dark mood"
Resolved: "Increase exposure by 10% while maintaining cool color temperature"
```

## Cultural & Context-Aware Examples

### Example 21: Festival Decoration
```
Original: Plain storefront
Edit: Add Chinese New Year decorations - red lanterns, gold "福" character, maintain store sign
```

### Example 22: Seasonal Update
```
Original: Summer landscape
Edit: Transform to autumn - change leaves to orange/red, add fallen leaves, cooler lighting
```

## Technical Specification Examples

### Example 23: Precise Positioning
```
element: company_logo
dimensions: 
  width: 200px
  height: 75px
position:
  x: 50px from left
  y: 50px from top
effects:
  shadow: 2px 2px 4px rgba(0,0,0,0.3)
  opacity: 100%
```

### Example 24: Color Specification
```
target: background_sky
current_color: #87CEEB (sky blue)
new_color: #FF6B9D (sunset pink)
gradient:
  type: linear
  direction: top-to-bottom
  stops: 
    - 0%: #FF6B9D
    - 100%: #FEC867
```

## Accessibility Examples

### Example 25: High Contrast Mode
```
Original: Low contrast design
Edit: Increase text contrast to WCAG AAA standard
- Text: Pure black (#000000)
- Background: Pure white (#FFFFFF)
- Borders: 2px solid black
```

## Animation Frame Examples

### Example 26: Motion Sequence
```
Frame 1: Ball at left side
Frame 2: Ball at center (this edit)
Frame 3: Ball at right side
Edit: Move ball to exact center, add motion blur trailing left
```

## Quality Assurance Examples

### Example 27: Resolution Enhancement
```
Input: 512x512 low quality
Process:
  - Upscale to 2048x2048
  - Enhance details
  - Reduce noise
  - Sharpen edges
Output: High-res version maintaining content
```

## Special Effects Examples

### Example 28: Reflection Addition
```
Object: Standing person
Edit: Add water puddle reflection below
Properties:
  - Ripple distortion
  - 50% opacity
  - Darker tone
  - Inverted vertically
```

### Example 29: Shadow Creation
```
Objects: Floating balloons
Edit: Add realistic shadows on ground
- Light source: top-left
- Shadow softness: medium
- Shadow color: dark gray
- Perspective: ground plane
```

### Example 30: Glow Effect
```
Target: Neon sign text
Edit: Add realistic neon glow
- Inner glow: bright white
- Outer glow: color-matched halo
- Intensity: high
- Spread: 20px radius
```

## Validation Examples

Each example demonstrates:
- Clear, specific instructions
- Preservation of important elements
- Realistic, achievable edits
- Proper text quotation
- Spatial precision
- Attribute detail