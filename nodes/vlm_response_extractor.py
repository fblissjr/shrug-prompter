"""Simple VLM response extractor node"""

class VLMResponseExtractor:
    """
    Extracts text response from ShrugPrompter context output.
    Handles both single and batch modes.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "context": ("*",),
                "index": ("INT", {"default": 0, "min": 0}),
            }
        }
    
    RETURN_TYPES = ("STRING", "LIST", "INT")
    RETURN_NAMES = ("text", "all_texts", "count")
    FUNCTION = "extract_response"
    CATEGORY = "VLM/Utils"
    
    def extract_response(self, context, index=0):
        """Extract text response from VLM context"""
        all_texts = []
        
        if not isinstance(context, dict):
            return ("", [], 0)
        
        # Handle batch mode with multiple responses
        if context.get("batch_mode") and "llm_responses" in context:
            responses = context["llm_responses"]
            for resp in responses:
                text = self._extract_text(resp)
                all_texts.append(text)
        
        # Handle single response mode
        elif "llm_response" in context:
            response = context["llm_response"]
            text = self._extract_text(response)
            all_texts.append(text)
        
        # Get the requested index
        if 0 <= index < len(all_texts):
            selected_text = all_texts[index]
        else:
            selected_text = all_texts[0] if all_texts else ""
        
        return (selected_text, all_texts, len(all_texts))
    
    def _extract_text(self, response):
        """Extract text content from various response formats"""
        if isinstance(response, str):
            return response
        
        if isinstance(response, dict):
            # OpenAI format
            if "choices" in response and response["choices"]:
                choice = response["choices"][0]
                if "message" in choice:
                    return choice["message"].get("content", "")
                elif "text" in choice:
                    return choice["text"]
            
            # Ollama format
            if "message" in response:
                return response["message"].get("content", "")
            
            # Direct content
            if "content" in response:
                return response["content"]
            
            # Error response
            if "error" in response:
                return f"Error: {response['error'].get('message', 'Unknown error')}"
        
        return str(response)


NODE_CLASS_MAPPINGS = {
    "VLMResponseExtractor": VLMResponseExtractor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VLMResponseExtractor": "VLM Response Extractor",
}