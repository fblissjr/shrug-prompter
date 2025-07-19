"""Convert text lists to various formats for compatibility"""

class TextListToString:
    """Convert a list of text strings to a single string with separators"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_list": ("LIST",),
                "separator": ("STRING", {"default": "|", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "convert"
    CATEGORY = "VLM/Utils"
    
    def convert(self, text_list, separator="|"):
        """Join text list with separator"""
        if not isinstance(text_list, list):
            return (str(text_list),)
        
        # Convert all items to strings and join
        text_strings = [str(item).strip() for item in text_list]
        joined = separator.join(text_strings)
        
        return (joined,)


class TextListIndexer:
    """Get a specific item from a text list by index"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_list": ("LIST",),
                "index": ("INT", {"default": 0, "min": 0}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "get_item"
    CATEGORY = "VLM/Utils"
    
    def get_item(self, text_list, index=0):
        """Get item at index from list"""
        if not isinstance(text_list, list):
            return (str(text_list),)
        
        if index >= len(text_list):
            # Return last item if index too high
            return (str(text_list[-1]) if text_list else "",)
        
        return (str(text_list[index]),)


NODE_CLASS_MAPPINGS = {
    "TextListToString": TextListToString,
    "TextListIndexer": TextListIndexer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextListToString": "Text List to String",
    "TextListIndexer": "Text List Indexer",
}