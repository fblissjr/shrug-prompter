# Experimental Format Exploration

## Format 1: Pipeline Notation
```
char| Woman, late 20s, auburn hair, white tee
s1| Morning bedroom, soft light | She wakes, stretches, sits | Fixed medium, push in
s2| Kitchen, steam rising | Pours tea, holds mug | Track to counter, hold
s3| Balcony, city view | Steps out, breathes | Through doorway
```
**Tokens:** ~110 (39% reduction)
**Pros:** Visual clarity, familiar from tables
**Cons:** Multiple delimiters might confuse

## Format 2: Narrative Flow
```
Woman, late 20s, auburn hair, white tee.
Morning bedroom where she wakes, stretches, sits as camera pushes in.
Kitchen where she pours tea, holds mug while camera tracks and holds.
Balcony where she steps out, breathes deep through doorway framing.
```
**Tokens:** ~95 (47% reduction!)
**Pros:** Natural reading, implicit structure, maximum compression
**Cons:** Less explicit scene breaks

## Format 3: Single-Line Scenes
```
Woman, late 20s, auburn hair, white tee
1: Morning bedroom, soft light - she wakes, stretches, sits - fixed push in
2: Kitchen, steam rising - pours tea, holds mug - track to counter  
3: Balcony, city haze - steps out, breathes - through doorway
```
**Tokens:** ~100 (44% reduction)
**Pros:** Clear numbering, dash separation
**Cons:** Might read as subtraction

## Format 4: Slash Notation
```
Woman, late 20s, auburn hair, white tee
Morning bedroom/wakes stretches sits/fixed push in
Kitchen steam/pours tea holds mug/track hold counter
Balcony city/steps out breathes/doorway frame
```
**Tokens:** ~85 (53% reduction!)
**Pros:** Ultra-compact, clear divisions
**Cons:** Sacrifices some readability

## Format 5: Colon-Leading
```
Woman, late 20s, auburn hair
:morning bedroom, she wakes and stretches, camera fixed then pushes
:kitchen with steam, she pours tea, camera tracks to counter
:balcony overlooking city, she steps out, shot through doorway
```
**Tokens:** ~90 (50% reduction)
**Pros:** Single delimiter, flows well
**Cons:** Unusual notation

## Format 6: Arrow Progression
```
Woman, late 20s, auburn hair → 
Bedroom morning → wakes, stretches, sits → fixed push in →
Kitchen steam → pours tea, holds mug → track to counter →
Balcony city → steps out, breathes → through doorway
```
**Tokens:** ~95 (47% reduction)
**Pros:** Shows progression/flow
**Cons:** Arrow might tokenize as multiple tokens

## Analysis & Recommendation

**Most Compressed:** Slash notation (53% reduction)
**Most Natural:** Narrative flow (47% reduction)  
**Best Balance:** Single-line with colons (44% reduction)

I recommend exploring **Narrative Flow** next because:
1. It leverages how LLMs naturally understand language
2. Nearly 50% token reduction
3. No special symbols to learn
4. Reads like a story treatment
5. Structure emerges from grammar not formatting