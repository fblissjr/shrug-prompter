# Qwen-Image DiffSynth Bridge Template

Integration template for qwen-image with DiffSynth-Studio's Chinese prompt patterns, supporting bilingual workflows.

## DiffSynth Prompt Structure

Based on DiffSynth-Studio's Kolors and Qwen patterns:

### 1. Poetic Chinese Description Pattern
```python
template = """
一幅{style}的{composition}，
{lighting_description}，
画中{subject_description}，
{action_or_pose}，
{environment_description}，
{atmosphere_description}
"""
```

### 2. QwenPrompt System (from DiffSynth)
```python
system_prompt = """
You are an English image describer. Your task is to translate a given Chinese image description 
into a concise and precise English description. Ensure that the imagery is vivid and descriptive, 
and include stylistic elements to enrich the description.

Key points:
1. Capture the essence and mood of the Chinese description
2. Add appropriate aesthetic words
3. Include stylistic descriptions if not specified
4. Keep under 200 words
"""
```

## Bilingual Edit Instruction Flow

### English Input → Chinese Processing → Chinese Output

```mermaid
English Instruction → Parse Components → Generate Chinese Structure → Apply Edit → Chinese Description
```

### Template Structure

```python
class QwenImageDiffSynthBridge:
    def __init__(self):
        self.task_mappings = {
            # English to Chinese task mappings
            "add": "添加",
            "remove": "移除",
            "replace": "替换",
            "modify": "修改",
            "enhance": "增强",
            "transform": "转换"
        }
        
        self.style_mappings = {
            # Style descriptors
            "realistic": "写实风格",
            "anime": "动漫风格",
            "oil painting": "油画风格",
            "watercolor": "水彩画风格",
            "vintage": "复古风格",
            "cyberpunk": "赛博朋克风格",
            "minimalist": "极简主义风格"
        }
```

## Complete Workflow Examples

### Example 1: Product Image Enhancement

**English Input:**
```
Add "LIMITED EDITION" badge to product photo with golden accent
```

**Chinese Structured Edit:**
```
编辑指令：在产品图片上添加限量版标识
具体要求：
- 标签文字："LIMITED EDITION"（保持英文）
- 标签样式：金色质感徽章
- 位置：右上角45度角
- 大小：占图像宽度20%
- 效果：金属光泽，轻微阴影
保持产品主体完整可见
```

**DiffSynth-Style Output:**
```
一幅精美的产品展示图，
柔和的摄影棚光线照明，
画中产品细节清晰可见，
右上角装饰着金色"LIMITED EDITION"徽章，
徽章呈现高级金属质感，
整体画面专业且富有商业美感
```

### Example 2: Portrait Style Transfer

**English Input:**
```
Transform portrait to anime style with blue hair and sparkles
```

**Chinese Structured Edit:**
```
编辑指令：将肖像转换为动漫风格
转换细节：
- 风格：日式动漫画风
- 头发颜色：改为蓝色渐变
- 特效：添加闪光粒子效果
- 眼睛：大眼睛动漫风格
- 皮肤：平滑处理，动漫质感
保持人物基本特征和姿态
```

**DiffSynth-Style Output:**
```
一幅充满二次元美感的动漫人物画，
梦幻的光线效果，
画中人物拥有渐变蓝色长发，
大而明亮的眼睛闪烁着光芒，
周围漂浮着星星般的闪光粒子，
整体氛围梦幻而唯美
```

## Advanced Integration Patterns

### 1. Negative Prompt Generation (Chinese)

```python
def generate_negative_prompt_chinese(task_type):
    base_negative = "低质量，模糊，变形，错误的比例"
    
    task_specific = {
        "portrait": "错误的眼睛，扭曲的面部，多余的肢体",
        "product": "错误的标签，模糊的文字，不协调的颜色",
        "landscape": "不自然的光线，错误的透视，混乱的构图",
        "text": "错别字，不清晰的字体，错误的排版"
    }
    
    return f"{base_negative}，{task_specific.get(task_type, '')}"
```

### 2. Style Description Enhancement

```python
def enhance_style_description_chinese(base_style):
    style_enhancements = {
        "写实": "超写实细节，真实的光影效果，自然的色彩过渡",
        "动漫": "精致的线条，鲜艳的色彩，日式美学特征",
        "油画": "厚重的笔触，丰富的层次，经典的色彩运用",
        "水彩": "透明的色彩层次，流动的水渍效果，柔和的边缘",
        "赛博朋克": "霓虹灯光，高科技元素，未来都市感"
    }
    
    return style_enhancements.get(base_style, base_style)
```

### 3. Spatial Relationship Description

```python
def describe_spatial_chinese(position, size, depth):
    position_desc = {
        "foreground": "前景突出",
        "midground": "中景平衡",
        "background": "背景衬托"
    }
    
    size_desc = {
        "small": "小巧精致",
        "medium": "适中大小",
        "large": "醒目突出"
    }
    
    return f"{position_desc[depth]}，{size_desc[size]}，位于{position}"
```

## Template Components

### 1. Image Analysis Template (Chinese)
```
图像分析：
- 主体：[主要对象及其特征]
- 背景：[环境和背景元素]
- 色调：[整体色彩倾向]
- 风格：[视觉风格特征]
- 构图：[画面布局结构]
```

### 2. Edit Instruction Template (Chinese)
```
编辑指令：
操作类型：{task_type}
目标元素：{target}
修改内容：
- {modification_1}
- {modification_2}
- {modification_3}
预期效果：{expected_result}
注意事项：{constraints}
```

### 3. Result Description Template (Chinese)
```
编辑结果描述：
画面呈现{overall_description}，
主要变化包括{main_changes}，
{element_1_description}，
{element_2_description}，
整体效果{final_impression}
```

## DiffSynth-Specific Patterns

### Kolors Prompt Pattern
```python
# From DiffSynth Kolors examples
kolors_template = """
一幅充满{aesthetic}的{scene_type}，
{skin_tone_description}，
画中{character_description}，
{clothing_description}，
{pose_and_expression}，
周围是{environment_elements}，
{lighting_and_atmosphere}
"""

# Example usage
prompt = kolors_template.format(
    aesthetic="诗意美感",
    scene_type="全身画",
    skin_tone_description="泛红的肤色",
    character_description="一位银色长发、蓝色眼睛的少女",
    clothing_description="身穿蓝色吊带连衣裙",
    pose_and_expression="漂浮在水下，面向镜头",
    environment_elements="光彩的气泡",
    lighting_and_atmosphere="和煦的阳光透过水面折射进水下"
)
```

### WAN Video Prompt Pattern
```python
# For video generation context
wan_template = """
场景设定：{scene_setting}
镜头运动：{camera_movement}
主体动作：{subject_action}
过渡效果：{transition_effect}
时长节奏：{timing_rhythm}
"""
```

## Practical Implementation

### Complete Bridge Function
```python
def qwen_diffsynth_bridge(english_input, mode="edit"):
    """
    Bridge between English input and Chinese processing for qwen-image
    with DiffSynth-Studio patterns
    """
    
    # Step 1: Parse English input
    components = parse_english_components(english_input)
    
    # Step 2: Generate Chinese structure
    if mode == "edit":
        chinese_instruction = generate_edit_instruction_chinese(components)
    elif mode == "generation":
        chinese_instruction = generate_kolors_style_prompt(components)
    elif mode == "video":
        chinese_instruction = generate_wan_style_prompt(components)
    
    # Step 3: Apply qwen-image processing
    result = process_with_qwen_image(chinese_instruction)
    
    # Step 4: Generate Chinese description of result
    chinese_description = describe_result_chinese(result)
    
    return {
        "english_input": english_input,
        "chinese_instruction": chinese_instruction,
        "chinese_description": chinese_description,
        "result": result
    }
```

### Helper Functions
```python
def parse_english_components(text):
    """Extract key components from English instruction"""
    return {
        "task": extract_task_verb(text),
        "target": extract_target_object(text),
        "attributes": extract_attributes(text),
        "position": extract_position(text),
        "style": extract_style_hints(text)
    }

def generate_edit_instruction_chinese(components):
    """Generate structured Chinese edit instruction"""
    template = """
    编辑任务：{task_zh}
    目标对象：{target}
    位置：{position_zh}
    属性：{attributes_zh}
    风格要求：{style_zh}
    """
    
    return template.format(
        task_zh=TASK_MAP[components["task"]],
        target=components["target"],
        position_zh=POSITION_MAP[components["position"]],
        attributes_zh=translate_attributes(components["attributes"]),
        style_zh=translate_style(components["style"])
    )

def describe_result_chinese(result):
    """Generate poetic Chinese description of the result"""
    # Use DiffSynth's poetic pattern
    return generate_poetic_description(result)
```

## Quality Assurance

### Validation Rules
1. **Text Preservation**: Original text in quotes must not be translated
2. **Position Accuracy**: Use precise Chinese spatial terms
3. **Style Consistency**: Match DiffSynth's descriptive patterns
4. **Cultural Appropriateness**: Use culturally relevant descriptions
5. **Technical Precision**: Include specific values and measurements

### Common Patterns to Follow
- Start descriptions with "一幅" (a picture of)
- Use "画中" (in the picture) to introduce subjects
- End with atmospheric descriptions
- Include sensory details (light, texture, mood)
- Maintain poetic flow in descriptions

This bridge template ensures seamless integration between English input, Chinese processing, and the DiffSynth-Studio ecosystem while maintaining the precision required for qwen-image operations.