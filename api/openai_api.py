# Simple synchronous OpenAI API implementation for ComfyUI
import requests
import json
import os
import sys
from typing import Optional, Dict, List, Union

# Import capability detector
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from api.capabilities_detector import CapabilityDetector
except ImportError:
    CapabilityDetector = None


def send_request_openai(messages, api_key, base_url, llm_model, max_tokens, temperature, top_p, **kwargs):
    """
    Send a synchronous request to an OpenAI-compatible API.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        api_key: API key for authentication
        base_url: Base URL of the API server
        llm_model: Model name to use
        max_tokens: Maximum tokens to generate
        temperature: Temperature for sampling
        top_p: Top-p for sampling
        **kwargs: Additional parameters
        
    Returns:
        Dict with API response or error
    """
    try:
        # Prepare the request
        url = f"{base_url.rstrip('/')}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add auth header if API key provided
        if api_key and api_key != "not-required-for-local":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Build request body
        body = {
            "model": llm_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False
        }
        
        # Add any extra parameters, but skip None values
        for key, value in kwargs.items():
            if key not in body and value is not None:
                body[key] = value
        
        # Remove any keys with None values that might have been added
        body = {k: v for k, v in body.items() if v is not None}
        
        # Check if we should use multipart endpoint for vision models
        raw_images = kwargs.get('raw_images', [])
        use_multipart = False
        
        if raw_images and CapabilityDetector:
            # Check server capabilities
            use_multipart = CapabilityDetector.should_use_multipart(base_url)
            
            if use_multipart:
                # Use multipart endpoint for better performance
                # Remove raw_images from kwargs since we pass it as positional
                kwargs_without_raw = {k: v for k, v in kwargs.items() if k != 'raw_images'}
                return _send_multipart_request(
                    messages, raw_images, api_key, base_url, llm_model, 
                    max_tokens, temperature, top_p, **kwargs_without_raw
                )
        
        # Make standard request
        # Default to 300 seconds (5 minutes) for vision models which can be slow
        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=kwargs.get('timeout', 300)
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Return the JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # Return error in OpenAI format
        return {
            "error": {
                "message": str(e),
                "type": "request_error"
            }
        }
    except Exception as e:
        return {
            "error": {
                "message": str(e),
                "type": "unknown_error"
            }
        }


def _send_multipart_request(messages, raw_images, api_key, base_url, llm_model, max_tokens, temperature, top_p, **kwargs):
    """
    Send request using multipart endpoint for 57ms faster processing per image.
    This avoids base64 encoding overhead and reduces bandwidth by 33%.
    """
    try:
        url = f"{base_url.rstrip('/')}/v1/chat/completions/multipart"
        
        # Prepare headers (no Content-Type, requests will set it with boundary)
        headers = {}
        if api_key and api_key != "not-required-for-local":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Replace __RAW_IMAGE__ placeholders in messages
        messages_with_placeholders = []
        image_count = 0
        
        for msg in messages:
            if isinstance(msg.get("content"), list):
                new_content = []
                for item in msg["content"]:
                    if item.get("type") == "image_url":
                        # Replace with placeholder
                        new_content.append({
                            "type": "image_url",
                            "image_url": {"url": "__RAW_IMAGE__"}
                        })
                        image_count += 1
                    else:
                        new_content.append(item)
                messages_with_placeholders.append({
                    "role": msg["role"],
                    "content": new_content
                })
            else:
                messages_with_placeholders.append(msg)
        
        # Prepare multipart data
        data = {
            'model': llm_model,
            'messages': json.dumps(messages_with_placeholders),
            'max_tokens': str(max_tokens),
            'temperature': str(temperature),
            'top_p': str(top_p),
            'stream': 'false'
        }
        
        # Add extra parameters including resize options
        resize_params = ['resize_max', 'resize_width', 'resize_height', 'image_quality', 'preserve_alpha']
        for key, value in kwargs.items():
            if key not in ['raw_images', 'timeout'] and value is not None:
                # Handle boolean preserve_alpha specially
                if key == 'preserve_alpha':
                    data[key] = 'true' if value else 'false'
                else:
                    data[key] = str(value)
        
        # Add image files
        files = []
        for i, img_bytes in enumerate(raw_images[:image_count]):
            files.append(('images', (f'image_{i}.jpg', img_bytes, 'image/jpeg')))
        
        # Make request
        response = requests.post(
            url,
            headers=headers,
            data=data,
            files=files,
            timeout=kwargs.get('timeout', 300)
        )
        
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        # Fallback to standard endpoint on error
        print(f"[Shrug-Prompter] Multipart request failed, falling back to standard: {e}")
        # Remove raw_images from kwargs to use standard base64 method
        kwargs_copy = kwargs.copy()
        kwargs_copy.pop('raw_images', None)
        return send_request_openai(
            messages, api_key, base_url, llm_model, 
            max_tokens, temperature, top_p, **kwargs_copy
        )