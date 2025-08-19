# Qwen-Image Chinese Prompt Template (DiffSynth Official)
# Source: examples/qwen_image/model_inference/*.py

## 系统提示 (System Prompt)
你是一位专业的图像描述专家，擅长创作适合Qwen-Image模型的中文提示词。你的描述应该具有诗意、画面感强、细节丰富。

## 提示词结构 (Prompt Structure)
[主题类型]，[主体描述]，[服装/外观]，[动作/姿态]，[环境/背景]，[光影效果]，[氛围/情绪]，[细节特征]，[风格修饰]。

## 关键词类别 (Keyword Categories)

### 主题类型
- 精致肖像 (Exquisite portrait)
- 唯美场景 (Beautiful scene)
- 梦幻画面 (Dreamy imagery)
- 写实风格 (Realistic style)
- 艺术创作 (Artistic creation)

### 人物描述
- 少女/女子/男子 (Girl/Woman/Man)
- 面容恬静 (Calm expression)
- 眼神灵动 (Vivid eyes)
- 发丝轻扬 (Hair gently floating)
- 优雅姿态 (Elegant posture)

### 服装描述
- 蓝裙飘逸 (Blue flowing dress)
- 白裙轻盈 (Light white dress)
- 和服典雅 (Elegant kimono)
- 现代服饰 (Modern clothing)

### 环境背景
- 水下世界 (Underwater world)
- 樱花纷飞 (Cherry blossoms falling)
- 春日庭院 (Spring courtyard)
- 森林背景 (Forest background)
- 天空宫殿 (Palace in the sky)

### 光影效果
- 光影透澈 (Clear light and shadow)
- 月光柔和 (Soft moonlight)
- 阳光温暖 (Warm sunlight)
- 光晕环绕 (Halo surrounding)
- 动态光影 (Dynamic lighting)

### 氛围词汇
- 梦幻唯美 (Dreamy and beautiful)
- 宁静祥和 (Peaceful and harmonious)
- 神秘莫测 (Mysterious)
- 温馨浪漫 (Warm and romantic)
- 细节精致 (Fine details)

## 示例提示词 (Example Prompts)

### 水下少女 (Underwater Girl)
精致肖像，水下少女，蓝裙飘逸，发丝轻扬，光影透澈，气泡环绕，面容恬静，细节精致，梦幻唯美。

### 樱花庭院小狗 (Dog in Cherry Blossom Courtyard)
一只小狗，毛发光洁柔顺，眼神灵动，背景是樱花纷飞的春日庭院，唯美温馨。

### 月下美人 (Beauty Under Moonlight)
月光下的美人，淡蓝长裙随风飘动，坐在悬崖顶端眺望远方，柔和光晕，远处飞鸟，海上孤帆，意境深远。

### 武士少女 (Samurai Girl)
武士少女身着和服，手持燃烧红焰的刀剑，长发随风飘动，一只小鸟停在手背，写实风格，细节丰富。

## 创作指南 (Creation Guidelines)

1. **简洁精炼**：使用逗号分隔的短语，避免冗长句子
2. **诗意表达**：采用富有诗意的词汇组合
3. **细节丰富**：包含具体的颜色、材质、光影描述
4. **层次分明**：从主体到背景，从整体到细节
5. **风格统一**：保持整体风格的一致性

## 提示词公式 (Prompt Formula)
[场景定位] + [主体特征] + [服装外观] + [动作姿态] + [环境描述] + [光影效果] + [细节补充] + [氛围渲染]

## 使用说明 (Usage Notes)
- Qwen-Image对中文提示词有良好支持
- 建议字数控制在50-100字之间
- 可以混合使用中英文，但保持主体语言一致
- 逗号分隔有助于模型理解不同要素