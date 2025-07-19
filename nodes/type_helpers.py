"""Helper nodes for type conversion"""

class AnyTypePassthrough:
    """Simple passthrough that accepts and returns any type"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("*",),
            }
        }
    
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("output",)
    FUNCTION = "passthrough"
    CATEGORY = "VLM/Utils"
    
    def passthrough(self, input):
        """Just pass through the input"""
        return (input,)


class ImageToAny:
    """Convert IMAGE type to generic * type"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("any",)
    FUNCTION = "convert"
    CATEGORY = "VLM/Utils"
    
    def convert(self, image):
        """Convert IMAGE to any type"""
        return (image,)


NODE_CLASS_MAPPINGS = {
    "AnyTypePassthrough": AnyTypePassthrough,
    "ImageToAny": ImageToAny,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AnyTypePassthrough": "Any Type Passthrough",
    "ImageToAny": "Image to Any Type",
}