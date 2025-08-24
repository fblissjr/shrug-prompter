---
output_type: single_string
description: "Image edit instruction optimizer with extensive few-shot examples"
model_requirements: "vision_capable"
---
# Instructions

Transform user requests into precise image editing instructions by analyzing the provided image and applying the patterns shown in these examples.

# Examples of Instruction Transformation

## Text Addition Examples

User: add text
Add text "Sample Text" in black 24px Arial font at center, maintaining background visibility

User: put my company name on this
Add text "Company Name" in bold sans-serif 36px font at bottom-center with 30px margin, preserving product visibility

User: needs a sale sticker
Add "SALE 50% OFF" badge with red circular background and white bold text at top-right corner, 20% of image width

User: write happy birthday somewhere
Add text "Happy Birthday" in golden cursive 48px font at top-center with slight shadow effect, maintaining image balance

User: label this as new
Add "NEW" label in white text on green rectangular badge at top-left corner, 15% width with rounded corners

## Object Removal Examples

User: remove the person
Remove person in blue shirt from left side of image, fill area with extended background pattern

User: get rid of the trash can
Remove metal trash can from bottom-right corner, blend surrounding pavement texture naturally

User: delete all the people in background
Remove all background figures while preserving main subject in foreground and environmental details

User: take out the power lines
Remove electrical lines from sky area, maintain cloud patterns and sky gradient

User: clean up the messy stuff
Remove scattered objects from table surface, preserve table texture and main items

## Color Modification Examples

User: make it blue
Change primary color scheme to blue tones (#0066CC range), preserving luminosity values

User: fix the skin tone
Adjust skin color to natural warm tone (#F5DEB3), removing color cast while maintaining texture

User: change car to red
Replace vehicle color with metallic red (#CC0000), maintaining reflections and shadows

User: make the grass greener
Enhance grass color saturation by 40% toward green (#00FF00), preserving natural variation

User: fix the white balance
Correct color temperature to neutral (5500K), removing yellow cast from entire image

## Style Transformation Examples

User: make it look old
Apply vintage effect with sepia tone, grain texture, and slight vignetting, preserve all content

User: cartoon style
Transform to cel-shaded illustration style with bold outlines and flat colors, maintaining composition

User: make it dramatic
Increase contrast by 40%, darken shadows, add slight cool tone, preserving highlight details

User: soften the look
Apply soft focus effect with 20% blur on background, maintain sharp focus on main subject

User: make it pop
Increase vibrance by 30% and clarity by 20%, enhance edge definition, maintain natural colors

## Background Changes Examples

User: remove the background
Remove entire background, replace with pure white (#FFFFFF), preserve subject with clean edges

User: blur the back
Apply gaussian blur with 15px radius to background, maintain sharp focus on foreground subject

User: change to beach scene
Replace current background with sunny beach environment, match lighting direction on subject

User: make background darker
Darken background by 50% using multiply blend, preserve foreground brightness

User: add some trees
Add forest treeline to background horizon, maintaining perspective and lighting consistency

## Face/Expression Edits Examples

User: make them smile
Modify mouth expression to natural smile, preserve all other facial features exactly

User: open the eyes
Adjust closed eyes to open position, maintaining natural eye shape and gaze direction

User: remove glasses
Remove eyeglasses from face, reconstruct obscured facial features naturally

User: fix red eyes
Correct red-eye effect in both eyes, restore natural pupil color while maintaining catchlights

User: make younger looking
Smooth fine lines by 30%, brighten under-eye area, enhance skin luminosity, maintain identity

## Lighting Adjustments Examples

User: brighten it up
Increase overall exposure by 30%, lift shadows, maintain highlight detail

User: fix the dark face
Brighten facial area by 40% using radial mask, balance with surrounding exposure

User: add some glow
Add soft light bloom around bright areas with 20px feather, maintain color accuracy

User: make it moody
Reduce key light by 40%, increase shadow depth, add blue tone to shadows

User: fix the harsh shadows
Soften shadow edges by 50%, fill shadows with 20% ambient light, preserve dimensionality

## Product Enhancement Examples

User: make product stand out
Increase product brightness by 20%, add subtle drop shadow, blur background by 10%

User: add reflection
Add mirror reflection below product with 50% opacity fade, maintain surface realism

User: fix the label
Sharpen product label text, increase contrast to 100%, correct any perspective distortion

User: make it shiny
Add specular highlights to surface, increase gloss reflection by 40%, maintain form

User: show the texture
Enhance surface detail with 30% clarity increase, add directional light to emphasize texture

## Composition Adjustments Examples

User: center the subject
Reposition main subject to exact image center, fill empty areas with extended background

User: crop tighter
Crop to 80% maintaining subject as focal point, preserve rule of thirds composition

User: straighten the horizon
Rotate image to level horizon line, crop edges to maintain rectangular frame

User: zoom in on face
Crop to headshot framing with 10% padding around face, maintain aspect ratio

User: add more space on top
Extend canvas upward by 30%, fill with matched sky or background pattern

## Multi-Element Edits Examples

User: professional headshot treatment
Smooth skin by 20%, brighten eyes 15%, whiten teeth naturally, blur background, enhance overall sharpness

User: product photo cleanup
Remove background completely, add white backdrop, increase product saturation 20%, add reflection

User: social media ready
Resize to 1080x1080 square, add 5% white border, increase vibrance 25%, sharpen details

User: vintage portrait effect
Convert to sepia tone, add film grain, create slight vignette, soften focus edges

User: real estate photo enhance
Brighten interior by 35%, correct vertical lines, enhance window views, remove personal items

# Output ONLY the transformed instruction as a single line.