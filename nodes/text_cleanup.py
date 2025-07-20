import re
import unicodedata

class TextCleanupNode:
    """
    Cleans up text from LLM responses for downstream processing.
    Specify operations as a comma-separated list.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "operations": ("STRING", {
                    "default": "trim,unicode", 
                    "multiline": False,
                }),
            },
            "optional": {
                "custom_replacements": ("STRING", {"multiline": True, "default": ""}),
                "max_length": ("INT", {"default": 0, "min": 0, "max": 10000}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("cleaned_text", "original_text", "char_count", "operations_applied")
    FUNCTION = "cleanup_text"
    CATEGORY = "VLM/Text"
    
    DESCRIPTION = """Operations (comma-separated):
- trim: Remove leading/trailing whitespace
- unicode: Normalize unicode characters (smart quotes → regular quotes)
- ascii: Remove all non-ASCII characters  
- newlines: Replace newlines with spaces
- collapse: Collapse multiple spaces into one
- quotes: Strip surrounding quotes
- lower: Convert to lowercase
- upper: Convert to uppercase
- title: Title case
- sentence: Sentence case
- nobrackets: Remove [bracketed] text
- noparens: Remove (parenthetical) text
- nopunct: Remove punctuation
- alphanumeric: Keep only letters and numbers
- custom: Apply custom replacements

Example: "trim,unicode,collapse,lower"
"""
    
    def cleanup_text(self, text, operations="trim,unicode", custom_replacements="", max_length=0):
        """
        Clean up text with specified operations.
        """
        original = text
        cleaned = text
        
        # Parse operations
        ops = [op.strip().lower() for op in operations.split(',')]
        applied_ops = []
        
        # Apply operations in order
        for op in ops:
            if op == 'trim':
                before = cleaned
                cleaned = cleaned.strip()
                if before != cleaned:
                    print(f"[TextCleanup] Trimmed: '{before}' -> '{cleaned}'")
                applied_ops.append('trim')
                
            elif op == 'unicode':
                # Replace common unicode punctuation with ASCII equivalents
                replacements = {
                    '\u2018': "'",  # Left single quote
                    '\u2019': "'",  # Right single quote  
                    '\u201C': '"',  # Left double quote
                    '\u201D': '"',  # Right double quote
                    '\u2013': '-',  # En dash
                    '\u2014': '--', # Em dash
                    '\u2026': '...', # Ellipsis
                    '\u00A0': ' ',  # Non-breaking space
                    '\u2022': '*',  # Bullet
                    '\u00B7': '*',  # Middle dot
                    '\u2010': '-',  # Hyphen
                    '\u2011': '-',  # Non-breaking hyphen
                    '\u2212': '-',  # Minus sign
                }
                for unicode_char, ascii_char in replacements.items():
                    cleaned = cleaned.replace(unicode_char, ascii_char)
                # Normalize remaining unicode
                cleaned = unicodedata.normalize('NFKD', cleaned)
                applied_ops.append('unicode')
                
            elif op == 'ascii':
                cleaned = ''.join(char for char in cleaned if ord(char) < 128)
                applied_ops.append('ascii')
                
            elif op == 'newlines':
                cleaned = cleaned.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                applied_ops.append('newlines')
                
            elif op == 'collapse':
                cleaned = re.sub(r'\s+', ' ', cleaned)
                applied_ops.append('collapse')
                
            elif op == 'quotes':
                if len(cleaned) >= 2:
                    if (cleaned[0] == cleaned[-1]) and cleaned[0] in ('"', "'"):
                        cleaned = cleaned[1:-1]
                applied_ops.append('quotes')
                
            elif op == 'lower':
                cleaned = cleaned.lower()
                applied_ops.append('lower')
                
            elif op == 'upper':
                cleaned = cleaned.upper()
                applied_ops.append('upper')
                
            elif op == 'title':
                cleaned = cleaned.title()
                applied_ops.append('title')
                
            elif op == 'sentence':
                if cleaned:
                    cleaned = cleaned[0].upper() + cleaned[1:].lower()
                applied_ops.append('sentence')
                
            elif op == 'nobrackets':
                cleaned = re.sub(r'\[.*?\]', '', cleaned)
                applied_ops.append('nobrackets')
                
            elif op == 'noparens':
                cleaned = re.sub(r'\(.*?\)', '', cleaned)
                applied_ops.append('noparens')
                
            elif op == 'nopunct':
                import string
                cleaned = cleaned.translate(str.maketrans('', '', string.punctuation))
                applied_ops.append('nopunct')
                
            elif op == 'alphanumeric':
                cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned)
                applied_ops.append('alphanumeric')
                
            elif op == 'custom' and custom_replacements:
                lines = custom_replacements.strip().split('\n')
                for line in lines:
                    if '|' in line:
                        old, new = line.split('|', 1)
                        cleaned = cleaned.replace(old, new)
                applied_ops.append('custom')
        
        # Apply max_length last
        if max_length > 0 and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
            applied_ops.append(f'truncate_{max_length}')
        
        char_count = len(cleaned)
        ops_summary = ', '.join(applied_ops) if applied_ops else 'none'
        
        return (cleaned, original, char_count, ops_summary)


class TextListCleanupNode:
    """
    Cleans up a list of text strings from batch LLM responses.
    Specify operations as a comma-separated list.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_list": ("LIST", {"forceInput": True}),
                "operations": ("STRING", {
                    "default": "trim,unicode,newlines,collapse", 
                    "multiline": False,
                }),
                "join_separator": ("STRING", {"default": "|"}),
            },
            "optional": {
                "custom_replacements": ("STRING", {"multiline": True, "default": ""}),
                "max_length": ("INT", {"default": 0, "min": 0, "max": 10000}),
            }
        }
    
    RETURN_TYPES = ("LIST", "LIST", "STRING", "STRING")
    RETURN_NAMES = ("cleaned_list", "original_list", "cleaned_joined", "operations_applied")
    FUNCTION = "cleanup_text_list"
    CATEGORY = "VLM/Text"
    DESCRIPTION = "See TextCleanup for available operations"
    
    def cleanup_text_list(self, text_list, operations="trim,unicode,newlines,collapse", 
                         join_separator="|", custom_replacements="", max_length=0):
        """
        Clean up a list of text strings.
        """
        if not isinstance(text_list, list):
            text_list = [str(text_list)]
        
        original_list = text_list.copy()
        cleaned_list = []
        
        # Create a TextCleanupNode instance to reuse its logic
        cleaner = TextCleanupNode()
        
        # Track operations applied
        all_ops = []
        
        for text in text_list:
            cleaned, _, _, ops = cleaner.cleanup_text(
                str(text), operations, custom_replacements, max_length
            )
            cleaned_list.append(cleaned)
            if ops and ops not in all_ops:
                all_ops.append(ops)
        
        # Join with specified separator for compatibility with nodes like WAN
        cleaned_joined = join_separator.join(cleaned_list)
        
        # Summary of operations
        ops_summary = all_ops[0] if all_ops else "none"
        
        return (cleaned_list, original_list, cleaned_joined, ops_summary)


NODE_CLASS_MAPPINGS = {
    "TextCleanup": TextCleanupNode,
    "TextListCleanup": TextListCleanupNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextCleanup": "Text Cleanup",
    "TextListCleanup": "Text List Cleanup",
}