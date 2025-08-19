---
output_type: single_string  
description: "WAN 2.2 negative prompt template - comprehensive quality and artifact prevention"
model_requirements: "text_capable"
---

# WAN 2.2 Negative Prompt Generator

Generate comprehensive negative prompts for WAN 2.2 video generation based on the official DiffSynth-Studio implementation patterns. These prompts prevent common quality issues and unwanted effects.

## Core Negative Categories

### Color and Exposure Issues
- 色调艳丽 (overly vibrant colors)
- 过曝 (overexposed)
- 欠曝 (underexposed)  
- 色彩失真 (color distortion)
- 饱和度过高 (oversaturated)
- 白平衡错误 (white balance errors)
- 颜色偏移 (color shift)

### Motion and Dynamics Problems  
- 静态 (static)
- 静止不动的画面 (motionless scene)
- 僵硬的动作 (stiff movement)
- 不自然的运动 (unnatural motion)
- 抖动 (jittery motion)
- 运动模糊过度 (excessive motion blur)
- 帧率不稳定 (unstable frame rate)

### Quality Degradation
- 最差质量 (worst quality)
- 低质量 (low quality)
- 粗糙 (rough/coarse)
- 模糊 (blurry)
- 噪点 (noise/grain)
- 压缩伪影 (compression artifacts)
- 像素化 (pixelated)
- 失焦 (out of focus)

### Anatomical Issues
- 多余的手指 (extra fingers)
- 畸形的手 (deformed hands)
- 错误的解剖结构 (incorrect anatomy)
- 比例失调 (disproportionate)
- 缺失的肢体 (missing limbs)
- 扭曲的面部 (distorted face)
- 不对称的眼睛 (asymmetrical eyes)

### Background Problems
- 杂乱的背景 (cluttered background)
- 不相关的物体 (irrelevant objects)
- 背景干扰 (background interference)
- 深度混乱 (depth confusion)
- 透视错误 (perspective errors)
- 环境不一致 (inconsistent environment)

### Technical Artifacts
- 重影 (ghosting)
- 闪烁 (flickering)
- 条纹 (banding)
- 锯齿 (aliasing)
- 摩尔纹 (moiré patterns)
- 光晕 (haloing)
- 色彩渗透 (color bleeding)

### Lighting Issues
- 过度曝光 (overexposure)
- 欠曝 (underexposure)
- 不一致的照明 (inconsistent lighting)
- 硬阴影 (harsh shadows)
- 缺少阴影 (missing shadows)
- 人工照明痕迹 (artificial lighting traces)

### Composition Problems
- 构图不良 (poor composition)
- 中心偏移 (off-center)
- 裁剪不当 (improper cropping)
- 边缘切断 (edge cutting)
- 比例错误 (wrong proportions)
- 景深混乱 (confused depth of field)

## Context-Specific Negatives

### For Human Subjects
- 多余的四肢 (extra limbs)
- 融合的手指 (fused fingers)
- 浮动的肢体 (floating limbs)
- 不自然的姿势 (unnatural pose)
- 面部畸变 (facial distortion)
- 皮肤纹理异常 (abnormal skin texture)

### For Objects and Equipment
- 变形的物体 (deformed objects)
- 不完整的结构 (incomplete structure)
- 材质错误 (wrong materials)
- 尺寸不协调 (inconsistent sizing)
- 物理违规 (physics violations)

### For Environments
- 重复的模式 (repetitive patterns)
- 不匹配的透视 (mismatched perspective)
- 环境断层 (environmental breaks)
- 不合理的空间 (unrealistic spaces)

### For Movement Scenes
- 运动轨迹错误 (incorrect motion paths)
- 速度不一致 (inconsistent speed)
- 重力违规 (gravity violations)
- 惯性错误 (inertia errors)

## Template Usage Instructions

1. **Analyze the positive prompt** to identify potential problem areas
2. **Select relevant categories** based on scene content and complexity
3. **Combine general quality terms** with specific contextual negatives
4. **Prioritize based on model weaknesses** and common failure modes
5. **Keep concise but comprehensive** - typically 50-100 negative terms

## Standard Negative Prompt Templates

### General Purpose (Baseline)
"worst quality, low quality, blurry, out of focus, static, motionless scene, deformed hands, extra fingers, incorrect anatomy, cluttered background, overexposed, underexposed, color distortion, compression artifacts, pixelated, noise, jittery motion, unnatural movement"

### Human-Focused Scenes
"worst quality, low quality, extra limbs, deformed hands, fused fingers, floating limbs, extra fingers, incorrect anatomy, disproportionate, asymmetrical eyes, distorted face, unnatural pose, abnormal skin texture, facial distortion, static pose, stiff movement"

### Technical/Equipment Scenes  
"worst quality, low quality, deformed objects, incomplete structure, wrong materials, inconsistent sizing, physics violations, technical artifacts, ghosting, flickering, banding, aliasing, perspective errors"

### Action/Movement Scenes
"static, motionless scene, stiff movement, unnatural motion, jittery motion, excessive motion blur, unstable frame rate, incorrect motion paths, inconsistent speed, gravity violations, inertia errors, frozen action"

### Environmental/Landscape
"cluttered background, irrelevant objects, background interference, depth confusion, perspective errors, inconsistent environment, repetitive patterns, mismatched perspective, environmental breaks, unrealistic spaces"

## Output Format

Generate a comprehensive negative prompt tailored to the specific scene and content type. Combine relevant terms from multiple categories as appropriate.

**Example Output:**
"worst quality, low quality, static, motionless scene, deformed hands, extra fingers, incorrect anatomy, disproportionate, cluttered background, overexposed, color distortion, compression artifacts, jittery motion, unnatural movement, physics violations, perspective errors, inconsistent lighting"