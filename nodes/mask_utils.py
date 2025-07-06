# In shrug-prompter/nodes/mask_utils.py
import torch

class ShrugMaskUtilities:
    """
    Utility node for advanced mask operations and transformations.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "operation": (["resize", "crop", "dilate", "erode", "combine"], {"default": "resize"}),
            },
            "optional": {
                "target_size": ("INT", {"default": 512, "min": 64, "max": 2048}),
                "additional_mask": ("MASK",),
                "kernel_size": ("INT", {"default": 3, "min": 1, "max": 15}),
            },
        }

    RETURN_TYPES = ("MASK", "STRING")
    RETURN_NAMES = ("processed_mask", "info")
    FUNCTION = "process_mask"
    CATEGORY = "Shrug Nodes/Utilities"

    def process_mask(self, mask, operation, target_size=512, additional_mask=None, kernel_size=3):
        info = []
        try:
            if operation == "resize":
                result_mask = self._resize_mask(mask, target_size)
                info.append(f"Resized to {target_size}x{target_size}")
            elif operation == "crop":
                result_mask = self._crop_mask(mask)
                info.append("Cropped to bounding box")
            # ... and so on for other operations
            else:
                result_mask = mask
                info.append(f"Unknown op: {operation}")
            return (result_mask, "\n".join(info))
        except Exception as e:
            return (mask, f"Error: {e}")

    def _resize_mask(self, mask: torch.Tensor, size: int):
        import torch.nn.functional as F
        return F.interpolate(mask.unsqueeze(0), size=(size, size), mode='nearest').squeeze(0)

    def _crop_mask(self, mask: torch.Tensor):
        non_zero = torch.nonzero(mask.squeeze())
        if len(non_zero) == 0: return mask
        min_y, min_x = non_zero.min(dim=0)[0]
        max_y, max_x = non_zero.max(dim=0)[0]
        return mask[:, min_y:max_y+1, min_x:max_x+1]
