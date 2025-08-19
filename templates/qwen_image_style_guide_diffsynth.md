# Qwen-Image Style Guide (DiffSynth Official)
# Comprehensive guide for both Chinese and English prompts

## Model Characteristics
- Qwen-Image excels at both Chinese and English prompts
- Trained on diverse artistic styles and photorealistic content
- Strong understanding of spatial relationships and entity control
- Responds well to poetic and technical descriptions

## Prompt Length Guidelines

### Chinese Prompts
- **Optimal**: 50-100 characters
- **Structure**: Comma-separated phrases (，)
- **Style**: Poetic, concise, evocative

### English Prompts
- **Optimal**: 100-200 words
- **Structure**: Comma-separated descriptions (,)
- **Style**: Detailed, narrative, technical

## Universal Quality Tags

### Essential Quality Modifiers
```
best quality, masterpiece, award winning, highly detailed
```

### Style Modifiers
```
photorealistic, concept art, splash art, whimsical, fantastic
intricate detailed, hyperdetailed, maximalist style
```

### Lighting Modifiers
```
ambient occlusion, dynamic lighting, cozy ambient lighting
soft glow, halation, dramatic lighting
```

### Atmosphere Modifiers
```
harmony, serenity, tranquility, mysterious, dramatic
```

## Style Presets

### Photorealistic Portrait
**Chinese**: 写实肖像，细节丰富，光影真实，肌理清晰，专业摄影
**English**: photorealistic portrait, skin texture details, professional photography, sharp focus, studio lighting

### Dreamy Fantasy
**Chinese**: 梦幻唯美，柔光环绕，色彩柔和，意境深远，童话风格
**English**: dreamy atmosphere, soft ethereal lighting, pastel colors, whimsical fantasy, fairytale aesthetic

### Cinematic Scene
**Chinese**: 电影质感，宽荧幕构图，景深效果，氛围渲染，故事感强
**English**: cinematic composition, wide aspect ratio, depth of field, atmospheric perspective, narrative scene

### Traditional Art
**Chinese**: 国画风格，水墨意境，留白艺术，东方美学，诗情画意
**English**: traditional ink painting style, oriental aesthetics, negative space, brushwork texture, poetic mood

### Anime/Illustration
**Chinese**: 动漫风格，赛璐璐上色，线条清晰，色彩鲜明，日系画风
**English**: anime style, cel shading, clean lineart, vibrant colors, Japanese illustration

## Color Palette Descriptions

### Warm Tones
**Chinese**: 暖色调，金黄夕阳，橙红渐变，温暖柔和
**English**: warm color palette, golden hour, orange-red gradient, cozy warmth

### Cool Tones
**Chinese**: 冷色调，蓝紫渐变，清冷月光，冰雪质感
**English**: cool color scheme, blue-purple gradient, cold moonlight, icy atmosphere

### Pastel
**Chinese**: 粉彩色调，马卡龙色系，柔和淡雅，梦幻浪漫
**English**: pastel colors, soft muted tones, candy colors, romantic palette

## Composition Guidelines

### Rule of Thirds
**Chinese**: 三分构图，主体偏置，视觉平衡
**English**: rule of thirds composition, off-center subject, balanced framing

### Centered
**Chinese**: 中心构图，对称平衡，庄重大气
**English**: centered composition, symmetrical balance, formal arrangement

### Dynamic Angle
**Chinese**: 动态视角，倾斜构图，张力十足
**English**: dynamic perspective, dutch angle, dramatic tension

## Common Prompt Patterns

### Pattern 1: Subject-First
```
[Subject] + [Appearance] + [Action] + [Environment] + [Lighting] + [Style]
```

### Pattern 2: Scene-First
```
[Scene Setting] + [Atmosphere] + [Subject] + [Details] + [Quality]
```

### Pattern 3: Narrative
```
[Story Context] + [Character] + [Moment] + [Emotion] + [Technical]
```

## Negative Prompts (What to Avoid)

### Standard Negative
```
low quality, blurry, pixelated, distorted, disfigured, bad anatomy,
extra limbs, missing fingers, ugly, duplicate, morbid, mutilated
```

### Style-Specific Negative
```
cartoon (when wanting realistic), realistic (when wanting anime),
3d render (when wanting 2d), photograph (when wanting painting)
```

## Advanced Techniques

### Emphasis Control
- **Parentheses**: (important element) - mild emphasis
- **Double**: ((very important)) - strong emphasis
- **Brackets**: [de-emphasized] - reduce importance

### Weight Syntax
- element:1.2 - increase weight by 20%
- element:0.8 - decrease weight by 20%

### Style Mixing
```
"50% anime style, 30% realistic, 20% watercolor"
"油画风格混合水彩，七分写实三分写意"
```

## Bilingual Prompt Examples

### Example 1: Underwater Portrait
**Chinese**: 精致肖像，水下少女，蓝裙飘逸，发丝轻扬，光影透澈，气泡环绕，面容恬静，细节精致，梦幻唯美
**English**: A detailed portrait of a girl underwater, wearing a blue flowing dress, hair gently floating, clear light and shadow, surrounded by bubbles, calm expression, fine details, dreamy and beautiful

### Example 2: Mountain Palace
**Chinese**: 云雾缭绕，山巅宫殿，日出东方，仙气飘渺，古建筑群，意境深远
**English**: Mist-shrouded mountain palace, sunrise illumination, ethereal atmosphere, ancient architecture, profound artistic conception

## Tips for Best Results

1. **Consistency**: Keep style consistent throughout prompt
2. **Specificity**: Be specific about colors, materials, lighting
3. **Balance**: Balance detail with clarity
4. **Testing**: Test variations to find optimal phrasing
5. **Language**: Choose language based on desired aesthetic
6. **Tags**: Always include quality and style tags
7. **Order**: Place most important elements first

## Model-Specific Optimizations

### For Qwen-Image Base
- Emphasis on detailed descriptions
- Works well with both languages
- Responds to artistic style references

### For Qwen-Image-Distill
- More efficient with shorter prompts
- Stronger style consistency
- Better at specific art styles

### For Qwen-Image-EliGen
- Optimized for entity control
- Requires structured entity prompts
- Best with mask guidance

## Cultural Considerations

### Chinese Aesthetic
- Emphasis on mood and atmosphere (意境)
- Poetic descriptions preferred
- Nature and harmony themes
- Subtle emotion expression

### Western Aesthetic
- Focus on technical accuracy
- Detailed physical descriptions
- Dynamic action and drama
- Explicit emotion display