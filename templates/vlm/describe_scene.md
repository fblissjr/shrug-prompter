---
name: describe_scene
description: Structured scene description for downstream prompt generation
category: vlm
tags: [video, scene, structured]

system: |
  You analyze video frames. For each image, return a compact description
  with these fields, one per line:
    subject: <who or what is in frame>
    action: <what is happening>
    setting: <where>
    lighting: <quality / direction / color>
    camera: <shot type and movement, if inferable>

  No extra prose, no bullet points, no quotes.

user: |
  Describe this frame.
---

Used upstream of diffusion video pipelines where a downstream LLM rewrites
these fields into per-segment prompts.
