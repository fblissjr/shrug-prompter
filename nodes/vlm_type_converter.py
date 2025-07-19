"""Simple type converter for VLM results"""

class VLMResultsToGeneric:
    """Converts VLM_RESULTS to generic type for compatibility"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vlm_results": ("VLM_RESULTS",),
            }
        }
    
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("output",)
    FUNCTION = "convert"
    CATEGORY = "VLM/Utils"
    
    def convert(self, vlm_results):
        """Simply pass through the results with generic type"""
        return (vlm_results,)


NODE_CLASS_MAPPINGS = {
    "VLMResultsToGeneric": VLMResultsToGeneric,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VLMResultsToGeneric": "VLM Results to Generic",
}