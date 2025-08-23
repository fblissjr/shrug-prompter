# Qwen-Image English to Chinese Template

Template for processing English instructions and generating Chinese edit descriptions, based on DiffSynth-Studio patterns and dataset analysis.

## System Prompt for Chinese Output

```
你是一个专业的图像编辑指令优化器。你的任务是将用户提供的英文编辑指令转换为精确、结构化的中文编辑描述，以便生成高质量的编辑结果。

请严格遵循以下规则：

1. **输出必须为中文**
2. **保持原始文本内容不翻译**（如品牌名、产品名等需要用引号标注）
3. **使用精确的空间定位词汇**
4. **详细描述视觉属性**
```

## Core Translation Pattern (Based on DiffSynth)

### Input Format (English)
```
Task: [ADD|REMOVE|REPLACE|MODIFY] [target] with [attributes] at [position]
```

### Output Format (Chinese)
```
编辑任务：[添加|删除|替换|修改] [目标对象]
位置：[具体位置描述]
属性：[颜色、大小、样式等详细属性]
保持不变：[需要保留的元素]
```

## Task-Specific Templates

### 1. Text Addition (English → Chinese)

**English Input:**
```
Add text "SALE 50% OFF" in red bold letters at top-right corner
```

**Chinese Output:**
```
在图像右上角添加文字"SALE 50% OFF"
文字属性：
- 颜色：红色（#FF0000）
- 字体：粗体
- 大小：占图像宽度的15%
- 背景：透明
保持原图其他元素不变
```

### 2. Object Manipulation (English → Chinese)

**English Input:**
```
Replace the blue car with a red motorcycle
```

**Chinese Output:**
```
将蓝色汽车替换为红色摩托车
替换细节：
- 原对象：蓝色汽车（位于中心）
- 新对象：红色摩托车
- 保持原有位置和比例
- 匹配场景光照和阴影
```

### 3. Style Transformation (English → Chinese)

**English Input:**
```
Apply vintage filter with sepia tone
```

**Chinese Output:**
```
应用复古滤镜效果
风格参数：
- 色调：棕褐色（怀旧效果）
- 对比度：轻微降低
- 颗粒感：添加细微噪点
- 边缘：轻微暗角效果
```

## Bilingual Processing Examples (DiffSynth Pattern)

### Example 1: E-commerce Enhancement
```python
# English instruction
instruction_en = "Add 'NEW ARRIVAL' badge to product image"

# Chinese structured output
instruction_zh = """
添加产品标签
标签内容："NEW ARRIVAL"（保持英文）
位置：左上角
样式：
- 背景：红色圆形徽章
- 文字：白色粗体
- 大小：图像宽度的20%
- 阴影：轻微投影增强立体感
"""
```

### Example 2: Social Media Template
```python
# English instruction
instruction_en = "Add Instagram handle @photographer at bottom"

# Chinese structured output
instruction_zh = """
添加社交媒体水印
文字内容："@photographer"（保持原文）
位置：底部居中
样式：
- 颜色：白色，50%透明度
- 字体：现代无衬线体
- 大小：适中（不影响主体）
- 边距：距底部20像素
"""
```

## Kolors/DiffSynth Integration Pattern

Based on the Kolors examples from DiffSynth:

### Poetry-Style Description (Chinese)
```python
# DiffSynth Kolors pattern
prompt_zh = """
一幅充满诗意美感的[场景类型]，
画中[主体描述]，
[动作/姿态描述]，
周围是[环境元素]，
[光线/氛围描述]
"""

# Example from dataset
prompt_zh = """
一幅充满诗意美感的全身画，
泛红的肤色，
画中一位银色长发、蓝色眼睛的少女，
身穿蓝色吊带连衣裙，
漂浮在水下，面向镜头，
周围是光彩的气泡，
和煦的阳光透过水面折射进水下
"""
```

### Negative Prompt Pattern (Chinese)
```python
negative_zh = """
半身，苍白的肤色，蜡黄的肤色，
错误的眼睛，糟糕的人脸，
变形，多余的肢体，
模糊的颜色，模糊，
重复，病态，残缺
"""
```

## Qwen-Image Edit Instruction Formatter

### Step 1: Parse English Input
```python
def parse_english_instruction(instruction):
    components = {
        "task": extract_task_type(instruction),  # add/remove/replace
        "target": extract_target(instruction),
        "attributes": extract_attributes(instruction),
        "position": extract_position(instruction)
    }
    return components
```

### Step 2: Generate Chinese Structure
```python
def generate_chinese_structure(components):
    zh_template = f"""
图像编辑指令：
任务类型：{map_task_to_chinese(components['task'])}
目标对象：{components['target']}
位置信息：{map_position_to_chinese(components['position'])}
视觉属性：
- {format_attributes_chinese(components['attributes'])}
执行要求：
- 保持图像整体风格一致
- 确保编辑自然融合
- 维持原有构图平衡
"""
    return zh_template
```

## Mapping Dictionaries

### Task Mapping
```python
TASK_MAP = {
    "add": "添加",
    "remove": "删除/移除",
    "replace": "替换",
    "modify": "修改",
    "change": "更改",
    "transform": "转换",
    "apply": "应用",
    "enhance": "增强"
}
```

### Position Mapping
```python
POSITION_MAP = {
    "top-left": "左上角",
    "top-center": "顶部中央",
    "top-right": "右上角",
    "center-left": "左侧中央",
    "center": "正中心",
    "center-right": "右侧中央",
    "bottom-left": "左下角",
    "bottom-center": "底部中央",
    "bottom-right": "右下角",
    "background": "背景",
    "foreground": "前景"
}
```

### Color Mapping
```python
COLOR_MAP = {
    "red": "红色",
    "blue": "蓝色",
    "green": "绿色",
    "yellow": "黄色",
    "black": "黑色",
    "white": "白色",
    "gray": "灰色",
    "orange": "橙色",
    "purple": "紫色",
    "pink": "粉色",
    "brown": "棕色",
    "gold": "金色",
    "silver": "银色"
}
```

## Advanced Chinese Templates

### 1. Detailed Object Description
```
对象描述模板：
主体：[对象类型]
外观特征：
- 颜色：[具体颜色及色调]
- 材质：[光滑/粗糙/金属/布料等]
- 大小：[相对或绝对尺寸]
- 形状：[几何形状或轮廓描述]
空间关系：
- 位置：[九宫格位置]
- 层次：[前景/中景/背景]
- 遮挡：[是否遮挡其他元素]
```

### 2. Scene Atmosphere Description
```
场景氛围模板：
整体色调：[暖色调/冷色调/中性色调]
光线描述：
- 光源方向：[顶光/侧光/逆光/环境光]
- 光线强度：[明亮/柔和/昏暗]
- 光线色温：[暖黄/冷白/自然光]
环境元素：
- 背景：[具体场景描述]
- 氛围：[宁静/活泼/神秘/梦幻]
- 时间：[清晨/正午/黄昏/夜晚]
```

### 3. Technical Specification (Chinese)
```
技术规格：
分辨率要求：[像素尺寸]
颜色模式：[RGB/CMYK]
文件格式：[JPG/PNG/TIFF]
质量设置：[高/中/低]
处理优先级：[速度优先/质量优先]
```

## Integration with Qwen Model

### System Message for Qwen
```python
system_message_zh = """
你是一个专业的图像编辑助手。根据用户的英文指令，生成详细的中文编辑描述。

要求：
1. 输出必须为结构化的中文描述
2. 保留所有品牌名、产品名的原文（加引号）
3. 使用专业的图像编辑术语
4. 提供具体的颜色值、尺寸和位置信息
5. 确保描述的可执行性和精确性

输出格式：
- 使用清晰的层级结构
- 包含所有必要的视觉参数
- 说明保持不变的元素
"""
```

## Validation Checklist (Chinese)

编辑指令验证清单：
- [ ] 任务类型明确（添加/删除/替换/修改）
- [ ] 目标对象清晰可识别
- [ ] 位置信息精确（使用九宫格或像素值）
- [ ] 颜色规格完整（名称+色值）
- [ ] 尺寸定义明确（像素/百分比/相对大小）
- [ ] 保留元素说明清楚
- [ ] 文本内容用引号标注
- [ ] 总字数控制在100字以内

## Usage Example

```python
def process_english_to_chinese(english_instruction):
    # Parse English
    components = parse_english_instruction(english_instruction)
    
    # Generate Chinese
    chinese_output = generate_chinese_structure(components)
    
    # Validate
    if validate_chinese_output(chinese_output):
        return chinese_output
    else:
        return refine_chinese_output(chinese_output)
```

This template bridges English input with Chinese output while maintaining the precision required by qwen-image and following DiffSynth-Studio's patterns for Chinese prompt generation.