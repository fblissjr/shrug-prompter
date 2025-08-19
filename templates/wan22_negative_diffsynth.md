# WAN 2.2 Negative Prompts (DiffSynth Official)
# Source: examples/wanvideo/model_inference/Wan2.2-*.py

## Standard Negative Prompt (Chinese + English)
色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走

## English Translation Categories

### Color/Exposure Issues
- Overly saturated colors (色调艳丽)
- Overexposed (过曝)
- Overall grayish tone (整体发灰)

### Motion/Static Issues
- Static (静态)
- Still/motionless (静止)
- Frozen frame (静止不动的画面)
- Walking backwards (倒着走)

### Quality Problems
- Blurry details (细节模糊不清)
- Worst quality (最差质量)
- Low quality (低质量)
- JPEG compression artifacts (JPEG压缩残留)

### Unwanted Elements
- Subtitles (字幕)
- Artwork/painting style (风格，作品，画作，画面)

### Anatomical Issues
- Ugly (丑陋的)
- Incomplete/defective (残缺的)
- Extra fingers (多余的手指)
- Poorly drawn hands (画得不好的手部)
- Poorly drawn face (画得不好的脸部)
- Deformed (畸形的)
- Disfigured (毁容的)
- Malformed limbs (形态畸形的肢体)
- Fused fingers (手指融合)
- Three legs (三条腿)

### Background Issues
- Cluttered background (杂乱的背景)
- Too many people in background (背景人很多)

## Usage Notes
- This negative prompt is used consistently across WAN 2.2 T2V and I2V models
- Helps prevent common video generation artifacts
- Combines Chinese and English terms for maximum effectiveness
- Can be adapted based on specific scene requirements