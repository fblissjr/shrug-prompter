# Qwen-Image Dataset Deep Analysis

## Comprehensive Positioning Vocabulary

### Precise Bounding Box Positions

#### Primary Grid Positions (9-point grid)
- **top-left corner** - exact upper left (0-20% x, 0-20% y)
- **top-center** - center of top edge (40-60% x, 0-20% y)  
- **top-right corner** - exact upper right (80-100% x, 0-20% y)
- **center-left** - middle of left edge (0-20% x, 40-60% y)
- **exact center** - dead center (40-60% x, 40-60% y)
- **center-right** - middle of right edge (80-100% x, 40-60% y)
- **bottom-left corner** - exact lower left (0-20% x, 80-100% y)
- **bottom-center** - center of bottom edge (40-60% x, 80-100% y)
- **bottom-right corner** - exact lower right (80-100% x, 80-100% y)

#### Quadrant Positions
- **upper-left quadrant** - (0-50% x, 0-50% y)
- **upper-right quadrant** - (50-100% x, 0-50% y)
- **lower-left quadrant** - (0-50% x, 50-100% y)
- **lower-right quadrant** - (50-100% x, 50-100% y)

#### Third-based Positions
- **left third** - (0-33% x)
- **center third** - (33-67% x)
- **right third** - (67-100% x)
- **upper third** - (0-33% y)
- **middle third** - (33-67% y)
- **lower third** - (67-100% y)

#### Edge and Margin Positions
- **10px from left edge**
- **20px from top edge**
- **30px from right border**
- **40px from bottom edge**
- **5% margin from left**
- **15% inset from top**
- **flush against right edge**
- **touching bottom border**

#### Diagonal and Angular Positions
- **45-degree angle from top-left**
- **diagonal across entire image**
- **upper-left to lower-right diagonal**
- **30-degree rotation at center**

#### Relative Positions
- **directly above the logo**
- **immediately below the text**
- **to the left of the person**
- **adjacent to the button**
- **overlapping the corner**
- **behind the subject**
- **in front of the background**
- **between the two objects**

#### Precise Pixel Coordinates
- **at coordinates (100, 250)**
- **spanning from (50, 50) to (200, 200)**
- **centered at pixel (512, 384)**
- **occupying bbox [0.2, 0.3, 0.8, 0.7]**

## Comprehensive Transformation Verbs

### Core Action Verbs
- **Add** - Insert new element
- **Remove** - Delete existing element
- **Replace** - Swap one element for another
- **Change** - Modify existing property
- **Modify** - Alter characteristics
- **Transform** - Convert style or appearance
- **Apply** - Add effect or filter
- **Enhance** - Improve quality or appearance
- **Adjust** - Fine-tune parameters
- **Convert** - Change format or type

### Specific Manipulation Verbs
- **Insert** - Place into specific location
- **Delete** - Completely remove
- **Swap** - Exchange positions
- **Substitute** - Use alternative
- **Update** - Modernize or refresh
- **Alter** - Change partially
- **Edit** - Make corrections
- **Revise** - Improve version
- **Refine** - Polish details
- **Optimize** - Improve efficiency

### Enhancement Verbs
- **Brighten** - Increase luminosity
- **Darken** - Decrease luminosity
- **Sharpen** - Increase clarity
- **Blur** - Reduce sharpness
- **Smooth** - Remove roughness
- **Intensify** - Increase strength
- **Soften** - Reduce harshness
- **Strengthen** - Add power
- **Diminish** - Reduce prominence
- **Amplify** - Increase effect

### Color Manipulation Verbs
- **Colorize** - Add color to grayscale
- **Desaturate** - Remove color intensity
- **Tint** - Add color cast
- **Recolor** - Change existing colors
- **Neutralize** - Remove color cast
- **Warm** - Add warm tones
- **Cool** - Add cool tones
- **Invert** - Reverse colors
- **Shift** - Move color values
- **Balance** - Equalize colors

### Spatial Manipulation Verbs
- **Move** - Change position
- **Shift** - Slight position change
- **Rotate** - Turn around axis
- **Flip** - Mirror horizontally/vertically
- **Scale** - Change size
- **Resize** - Adjust dimensions
- **Crop** - Cut to smaller area
- **Extend** - Make larger
- **Stretch** - Elongate dimension
- **Compress** - Reduce space

### Style Transfer Verbs
- **Stylize** - Apply artistic style
- **Modernize** - Update appearance
- **Vintageize** - Make look old
- **Cartoonize** - Convert to cartoon
- **Animate** - Add motion effect
- **Dramatize** - Increase drama
- **Romanticize** - Add romantic mood
- **Professionalize** - Make business-ready
- **Casualize** - Make informal
- **Formalize** - Make official

## Dataset Vocabulary Patterns

### Size Descriptors
- **tiny** (< 5% of image)
- **small** (5-15% of image)
- **medium-sized** (15-30% of image)
- **large** (30-50% of image)
- **prominent** (50-70% of image)
- **dominant** (> 70% of image)
- **subtle** (barely visible)
- **bold** (highly visible)
- **oversized** (larger than expected)
- **miniature** (smaller than expected)

### Color Vocabulary
- **vibrant** - highly saturated
- **muted** - low saturation
- **pastel** - light and soft
- **neon** - bright glowing
- **metallic** - shiny metal-like
- **gradient** - color transition
- **monochrome** - single color
- **multicolored** - many colors
- **iridescent** - rainbow-like
- **translucent** - semi-transparent

### Texture Descriptors
- **smooth** - no roughness
- **rough** - uneven surface
- **glossy** - shiny surface
- **matte** - non-reflective
- **textured** - visible pattern
- **grainy** - small particles
- **silky** - smooth flowing
- **coarse** - rough texture
- **polished** - highly refined
- **weathered** - aged appearance

### Style Descriptors
- **minimalist** - simple clean
- **ornate** - highly decorated
- **modern** - contemporary style
- **vintage** - old-fashioned
- **retro** - past era style
- **futuristic** - sci-fi appearance
- **elegant** - refined graceful
- **casual** - informal relaxed
- **professional** - business-like
- **artistic** - creative style

### Lighting Terms
- **backlit** - light from behind
- **rim-lit** - edge lighting
- **soft-lit** - diffused light
- **harsh-lit** - strong direct light
- **ambient** - surrounding light
- **dramatic** - strong contrast
- **natural** - sunlight-like
- **studio** - controlled lighting
- **moody** - atmospheric
- **bright** - well-illuminated

## High-Quality Instruction Examples

### Professional Photography Retouching

**Example 1: Portrait Enhancement**
```
Remove temporary blemishes from face, smooth skin texture by 30% preserving pores, brighten eyes by 10%, even skin tone across forehead and cheeks, maintain all permanent features and natural character
```
- Verb: Remove, smooth, brighten, even, maintain
- Target: blemishes, skin, eyes, tone, features
- Spatial: face, forehead, cheeks
- Attributes: 30% smooth, 10% brighter
- Context: preserve pores, permanent features

**Example 2: Full Body Contouring**
```
Enhance muscle definition with -10% shadows in valleys and +10% highlights on peaks, smooth cellulite by 40% on thighs, tighten waistline by 2% maximum, maintain natural proportions and authentic appearance
```
- Verb: Enhance, smooth, tighten, maintain
- Target: muscles, cellulite, waistline
- Spatial: valleys, peaks, thighs
- Attributes: -10% shadows, +10% highlights, 40% smooth, 2% tighten
- Context: natural proportions, authentic

### E-commerce Product Photography

**Example 3: Product on White**
```
Remove background completely, replace with pure white #FFFFFF, add subtle drop shadow 20px below product at 30% opacity, place "NEW ARRIVAL" badge in red at top-left corner 50px from edges
```
- Verb: Remove, replace, add, place
- Target: background, shadow, badge
- Spatial: below product, top-left corner, 50px from edges
- Attributes: pure white, 20px shadow, 30% opacity, red color
- Context: complete removal, subtle effect

**Example 4: Sale Overlay**
```
Add circular red badge 100px diameter at top-right corner with 10px margin, insert "50% OFF" in white bold 24px font centered in badge, apply slight drop shadow 2px blur for depth
```
- Verb: Add, insert, apply
- Target: badge, text, shadow
- Spatial: top-right corner, centered in badge
- Attributes: 100px diameter, red, white bold 24px, 2px blur
- Context: 10px margin, depth effect

### Social Media Content

**Example 5: Instagram Story**
```
Crop to 9:16 aspect ratio centering main subject, add "@username" watermark in white at bottom-right 30px from edges with 60% opacity, apply warm filter with +10% orange in highlights
```
- Verb: Crop, add, apply
- Target: aspect ratio, watermark, filter
- Spatial: centering subject, bottom-right, highlights
- Attributes: 9:16 ratio, white text, 60% opacity, +10% orange
- Context: main subject centered, 30px margins

**Example 6: YouTube Thumbnail**
```
Increase contrast by 25% globally, add red arrow pointing from left-center to main subject, place "MUST SEE!" text in yellow 48px Impact font at top with black outline 3px
```
- Verb: Increase, add, place
- Target: contrast, arrow, text
- Spatial: globally, left-center to subject, top
- Attributes: 25% increase, red arrow, yellow 48px Impact, 3px outline
- Context: pointing to subject

### Real Estate Photography

**Example 7: Property Listing**
```
Straighten vertical lines to correct 3-degree tilt, brighten interior by 20% while preserving window detail, add property price "$450,000" in white on black gradient bar at bottom-left
```
- Verb: Straighten, brighten, add
- Target: vertical lines, interior, price
- Spatial: 3-degree correction, interior, bottom-left
- Attributes: 20% brighter, white text, black gradient
- Context: preserve window detail

**Example 8: Virtual Staging**
```
Add modern gray sofa centered against back wall, place glass coffee table 3 feet in front of sofa, insert "VIRTUALLY STAGED" disclaimer at bottom-center in italic gray 14px font
```
- Verb: Add, place, insert
- Target: sofa, table, disclaimer
- Spatial: against back wall, 3 feet in front, bottom-center
- Attributes: modern gray, glass, italic gray 14px
- Context: centered, proper spacing

### Document Processing

**Example 9: Business Document**
```
Add page number "Page 3 of 10" at bottom-center 30px from edge in Arial 10pt, apply "CONFIDENTIAL" watermark diagonally at 20% opacity, increase text contrast by 40% for readability
```
- Verb: Add, apply, increase
- Target: page number, watermark, contrast
- Spatial: bottom-center, diagonal, text areas
- Attributes: Arial 10pt, 20% opacity, 40% increase
- Context: 30px from edge, readability

**Example 10: Scanned Archive**
```
Remove yellow paper tint with color correction, straighten 2-degree clockwise rotation, add timestamp "Archived: 2024-01-15" at top-right in gray 9pt italic font
```
- Verb: Remove, straighten, add
- Target: tint, rotation, timestamp
- Spatial: paper area, 2-degree, top-right
- Attributes: color correction, gray 9pt italic
- Context: clockwise rotation

### Artistic Transformations

**Example 11: Oil Painting Effect**
```
Apply oil painting style with visible brushstrokes 15px width, increase color saturation by 20%, add canvas texture overlay at 30% opacity, maintain original composition and subject clarity
```
- Verb: Apply, increase, add, maintain
- Target: style, saturation, texture
- Spatial: entire image, overlay
- Attributes: 15px brushstrokes, 20% saturation, 30% opacity
- Context: preserve composition and clarity

**Example 12: Vintage Photography**
```
Convert to sepia tone with brown tint #8B7355, add film grain at 15% intensity, apply vignette darkening 20% at edges, create slight blur 2px at corners for authentic vintage look
```
- Verb: Convert, add, apply, create
- Target: tone, grain, vignette, blur
- Spatial: entire image, edges, corners
- Attributes: #8B7355 brown, 15% grain, 20% vignette, 2px blur
- Context: authentic vintage appearance

### Fashion Photography

**Example 13: Editorial Retouch**
```
Smooth skin to magazine quality 40% while preserving texture, elongate legs by 3% maintaining proportions, enhance eye makeup colors by 30% saturation, add subtle rim light along body contour
```
- Verb: Smooth, elongate, enhance, add
- Target: skin, legs, makeup, rim light
- Spatial: skin areas, legs, eyes, body contour
- Attributes: 40% smooth, 3% longer, 30% saturation
- Context: preserve texture, maintain proportions

**Example 14: Runway Photography**
```
Increase fashion garment contrast by 35%, remove runway background distractions, add motion blur 10px to background crowd, sharpen model and outfit details by 20%
```
- Verb: Increase, remove, add, sharpen
- Target: contrast, distractions, blur, details
- Spatial: garment, background, crowd, model
- Attributes: 35% contrast, 10px blur, 20% sharper
- Context: fashion focus

### Architectural Photography

**Example 15: Interior Design**
```
Balance window exposure recovering 30% highlight detail, warm interior lighting by adding +15% orange to midtones, remove electrical outlets from wall at coordinates (420, 380)
```
- Verb: Balance, warm, remove
- Target: exposure, lighting, outlets
- Spatial: windows, midtones, coordinates (420, 380)
- Attributes: 30% recovery, +15% orange
- Context: interior atmosphere

These examples demonstrate the complete pattern of high-quality instructions with clear verbs, specific targets, precise positioning, detailed attributes, and context preservation notes.