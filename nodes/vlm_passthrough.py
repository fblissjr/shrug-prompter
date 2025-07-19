"""Zero-copy VLM image passthrough node"""

import torch
from typing import Tuple

class VLMImagePassthrough:
    """
    Simple passthrough node that returns image references without copying.
    Use this when you want to send original images to VLM without any processing.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE", "INT")
    RETURN_NAMES = ("images", "original", "count")
    FUNCTION = "passthrough"
    CATEGORY = "VLM/Processing"
    
    def passthrough(self, images) -> Tuple:
        """Simply return references to the input images"""
        count = images.shape[0] if hasattr(images, 'shape') and images.dim() == 4 else 1
        
        # Return the same tensor reference twice - no copying!
        return (images, images, count)


class VLMImageResizer:
    """
    Minimal image resizer that only creates copies when actually resizing.
    More memory efficient than VLMImageProcessor.
    """
    
    @classmethod  
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "max_size": (["original", "256", "384", "512", "768", "1024"], {"default": "original"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "resize"
    CATEGORY = "VLM/Processing"
    
    def resize(self, images, max_size):
        """Resize only if needed, return original otherwise"""
        if max_size == "original":
            return (images,)
        
        target = int(max_size)
        B, H, W, C = images.shape
        
        # Return original if already small enough
        if max(H, W) <= target:
            return (images,)
        
        # Only create a copy when we actually need to resize
        with torch.no_grad():
            # Calculate new dimensions
            if H > W:
                new_h = target
                new_w = int(W * target / H)
            else:
                new_w = target
                new_h = int(H * target / W)
            
            # Resize
            resized = images.permute(0, 3, 1, 2)  # BHWC to BCHW
            resized = torch.nn.functional.interpolate(
                resized, size=(new_h, new_w), mode='bilinear', align_corners=False
            )
            resized = resized.permute(0, 2, 3, 1)  # BCHW to BHWC
            
        return (resized,)


NODE_CLASS_MAPPINGS = {
    "VLMImagePassthrough": VLMImagePassthrough,
    "VLMImageResizer": VLMImageResizer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VLMImagePassthrough": "VLM Image Passthrough (Zero Copy)",
    "VLMImageResizer": "VLM Image Resizer (Minimal)",
}