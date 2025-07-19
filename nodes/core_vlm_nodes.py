"""
Core VLM nodes with automatic memory management and efficient data handling.
Designed to minimize memory usage and automatically clean up after operations.
"""

import torch
import gc
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple
import weakref
from PIL import Image
import io
import base64

# Global memory manager that tracks allocations
class MemoryTracker:
    """Singleton memory tracker that monitors and cleans up automatically"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tensors = []
            cls._instance._arrays = []
        return cls._instance
    
    def register_tensor(self, tensor):
        """Register a tensor for tracking"""
        # Use weak references in a list instead of WeakSet
        # because tensors can't be hashed
        try:
            weak_ref = weakref.ref(tensor)
            self._tensors.append(weak_ref)
        except TypeError:
            # Some tensors may not be weakly referenceable
            pass
    
    def register_array(self, array):
        """Register a numpy array for tracking"""
        try:
            weak_ref = weakref.ref(array)
            self._arrays.append(weak_ref)
        except TypeError:
            pass
    
    def cleanup(self, force=False):
        """Clean up unused memory"""
        # Clear dead references from lists
        self._tensors = [ref for ref in self._tensors if ref() is not None]
        self._arrays = [ref for ref in self._arrays if ref() is not None]
        
        if force or len(self._tensors) > 10 or len(self._arrays) > 10:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

memory_tracker = MemoryTracker()


class VLMPrompter:
    """
    Core VLM prompter with automatic memory management.
    Processes images efficiently without keeping unnecessary copies in memory.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "system_prompt": ("STRING", {"multiline": True, "default": "You are a helpful assistant."}),
                "user_prompt": ("STRING", {"multiline": True, "default": "Describe this image."}),
                "max_tokens": ("INT", {"default": 512, "min": 1, "max": 2048}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "context": ("VLM_CONTEXT",),
                "seed": ("INT", {"default": -1}),
                "image_size": (["auto", "256", "384", "512", "768", "1024", "original"], {"default": "auto"}),
            }
        }
    
    RETURN_TYPES = ("VLM_RESULTS",)
    RETURN_NAMES = ("results",)
    FUNCTION = "process_images"
    CATEGORY = "VLM/Core"
    
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
    
    def process_images(self, images, system_prompt, user_prompt, max_tokens, temperature, top_p, context=None, seed=-1, image_size="auto"):
        """
        Process images with automatic memory management.
        Images are processed one at a time and memory is freed immediately.
        """
        if context is None:
            raise ValueError("VLM context required. Please connect a VLMProviderConfig node.")
        
        # Register input tensor for tracking
        if isinstance(images, torch.Tensor):
            memory_tracker.register_tensor(images)
        
        results = {
            "responses": [],
            "metadata": {
                "total_images": len(images) if hasattr(images, '__len__') else 1,
                "model": context.get("provider_config", {}).get("llm_model", "unknown") if isinstance(context, dict) and "provider_config" in context else context.get("llm_model", "unknown"),
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }
        
        try:
            # Process images one at a time to minimize memory usage
            if images.dim() == 4:  # Batch of images
                for i in range(images.shape[0]):
                    # Extract single image without copying
                    single_image = images[i:i+1]
                    
                    # Process and immediately append result
                    response = self._process_single_image(
                        single_image, system_prompt, user_prompt, 
                        max_tokens, temperature, top_p, context, seed, image_size
                    )
                    results["responses"].append(response)
                    
                    # Clean up after each image
                    if i % 3 == 0:
                        memory_tracker.cleanup()
            else:
                # Single image
                response = self._process_single_image(
                    images, system_prompt, user_prompt,
                    max_tokens, temperature, top_p, context, seed, image_size
                )
                results["responses"].append(response)
        
        finally:
            # Always clean up, even if error occurs
            memory_tracker.cleanup(force=True)
        
        return (results,)
    
    def _process_single_image(self, image_tensor, system_prompt, user_prompt, max_tokens, temperature, top_p, context, seed, image_size):
        """Process a single image efficiently"""
        # Convert to raw bytes for multipart or base64 for standard
        with torch.no_grad():
            # Move to CPU if needed, but don't copy
            if image_tensor.is_cuda:
                image_tensor = image_tensor.cpu()
            
            # Convert to numpy without copy if possible
            image_np = image_tensor.squeeze(0).numpy()
            
            # Convert to PIL Image
            image_np = (image_np * 255).astype(np.uint8)
            pil_image = Image.fromarray(image_np)
            
            # Get raw JPEG bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format="JPEG", quality=85, optimize=True)
            img_bytes = buffer.getvalue()
            buffer.close()
            
            # Free the numpy array and PIL image immediately
            del image_np
            del pil_image
        
        # Make API call
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        try:
            from shrug_router import send_request
        except ImportError:
            from ..shrug_router import send_request
        
        # Check if we should use multipart (raw bytes) for better performance
        # Import capability detector
        try:
            from ..api.capabilities_detector import CapabilityDetector
        except ImportError:
            CapabilityDetector = None
        
        # Handle both flat and nested context structures
        if isinstance(context, dict) and "provider_config" in context:
            provider_config = context["provider_config"]
        else:
            provider_config = context
            
        base_url = provider_config.get("base_url", "")
        use_multipart = False
        
        if CapabilityDetector and base_url:
            use_multipart = CapabilityDetector.should_use_multipart(base_url)
        
        if use_multipart:
            # For multipart, we'll pass raw bytes
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": "__RAW_IMAGE__"}}
                ]}
            ]
        else:
            # Standard base64 encoding
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]}
            ]
        
        kwargs = {
            "provider": provider_config["provider"],
            "base_url": provider_config["base_url"],
            "api_key": provider_config["api_key"],
            "llm_model": provider_config["llm_model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed if seed >= 0 else None
        }
        
        # Add raw images if using multipart
        if use_multipart:
            kwargs["raw_images"] = [img_bytes]
            
            # Use image_size parameter for server-side resizing
            if image_size != "auto" and image_size != "original":
                kwargs["resize_max"] = int(image_size)
            
            # Default quality settings for VLMPrompter
            kwargs["image_quality"] = 85
            kwargs["preserve_alpha"] = False
        
        try:
            response = send_request(**kwargs)
            # Extract just the text content, don't keep the full response
            if isinstance(response, dict) and "choices" in response:
                return response["choices"][0]["message"]["content"]
            return str(response)
        finally:
            # Clean up image data
            del img_bytes
            if 'img_b64' in locals():
                del img_b64


class VLMImageProcessor:
    """
    Unified image processor with automatic memory management.
    Replaces multiple image processing nodes with one efficient implementation.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mode": (["optimize_for_vlm", "prepare_for_video", "both"], {"default": "optimize_for_vlm"}),
                "size": (["256", "384", "512", "768", "1024", "original"], {"default": "384"}),
                "quality": (["draft", "balanced", "high"], {"default": "balanced"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE", "INT")
    RETURN_NAMES = ("processed", "original", "count")
    FUNCTION = "process_images"
    CATEGORY = "VLM/Processing"
    
    def process_images(self, images, mode, size, quality):
        """Process images with minimal memory usage"""
        # Quality to JPEG settings
        quality_map = {
            "draft": 70,
            "balanced": 85,
            "high": 95
        }
        jpeg_quality = quality_map[quality]
        
        # Size mapping
        if size != "original":
            target_size = int(size)
        else:
            target_size = None
        
        # Register input for tracking
        memory_tracker.register_tensor(images)
        
        count = images.shape[0] if images.dim() == 4 else 1
        
        # Process based on mode
        if mode == "both":
            # Return processed and original separately
            # Only clone if we need to resize, otherwise return views
            if target_size is not None:
                processed = self._process_for_vlm(images.clone(), target_size, jpeg_quality)
                original = images
            else:
                # Both are the same, just return views
                processed = images
                original = images
        elif mode == "optimize_for_vlm":
            if target_size is not None:
                # Create new tensor only if resizing
                processed = self._process_for_vlm(images.clone(), target_size, jpeg_quality)
            else:
                processed = images
            # For VLM mode, we don't need original
            original = processed  # Just a view, no copy
        else:  # prepare_for_video
            processed = self._process_for_video(images)
            original = processed  # Just a view, no copy
        
        # Clean up
        memory_tracker.cleanup()
        
        return (processed, original, count)
    
    def _process_for_vlm(self, images, target_size, jpeg_quality):
        """Optimize images for VLM processing - operates on already cloned tensor"""
        if target_size is None:
            return images
        
        B, H, W, C = images.shape
        
        # Skip if already smaller than target
        if max(H, W) <= target_size:
            return images
        
        # Calculate new dimensions
        if H > W:
            new_h = target_size
            new_w = int(W * target_size / H)
        else:
            new_w = target_size
            new_h = int(H * target_size / W)
        
        # Resize in-place on the cloned tensor
        images = images.permute(0, 3, 1, 2)  # BHWC to BCHW
        images = torch.nn.functional.interpolate(
            images, size=(new_h, new_w), mode='bilinear', align_corners=False
        )
        images = images.permute(0, 2, 3, 1)  # BCHW to BHWC
        
        return images
    
    def _process_for_video(self, images):
        """Prepare images for video generation"""
        # Ensure dimensions are divisible by 8 for video models
        B, H, W, C = images.shape
        new_h = (H // 8) * 8
        new_w = (W // 8) * 8
        
        if new_h != H or new_w != W:
            # Return a view, not a copy - this is just cropping
            return images[:, :new_h, :new_w, :]
        
        return images


class VLMResultCollector:
    """
    Efficient result collector that doesn't duplicate data.
    Uses weak references to avoid keeping results in memory unnecessarily.
    """
    
    def __init__(self):
        self._collectors = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "results": ("VLM_RESULTS",),
                "collector_id": ("STRING", {"default": "default"}),
            },
            "optional": {
                "reset": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("VLM_COLLECTION", "INT", "LIST")
    RETURN_NAMES = ("collection", "count", "text_list")
    FUNCTION = "collect_results"
    CATEGORY = "VLM/Results"
    
    def collect_results(self, results, collector_id="default", reset=False):
        """Collect results without duplicating data"""
        # Get or create collector
        if reset or collector_id not in self._collectors:
            collector = {
                "responses": [],
                "metadata": {}
            }
            self._collectors[collector_id] = collector
        else:
            collector = self._collectors[collector_id]
        
        # Add new responses (just references, not copies)
        new_responses = results.get("responses", [])
        collector["responses"].extend(new_responses)
        
        # Update metadata
        collector["metadata"].update(results.get("metadata", {}))
        
        # Create lightweight output
        count = len(collector["responses"])
        text_list = collector["responses"]  # Just a reference
        
        # Clean up old collectors
        if len(self._collectors) > 5:
            # Keep only the 5 most recent
            keys = list(self._collectors.keys())
            for key in keys[:-5]:
                del self._collectors[key]
        
        return (collector, count, text_list)


class VLMResultIterator:
    """
    Efficient iterator that doesn't copy data.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "collection": ("VLM_COLLECTION",),
                "index": ("INT", {"default": 0, "min": 0}),
            }
        }
    
    RETURN_TYPES = ("STRING", "INT", "BOOLEAN")
    RETURN_NAMES = ("text", "total_count", "has_more")
    FUNCTION = "get_result"
    CATEGORY = "VLM/Results"
    
    def get_result(self, collection, index=0):
        """Get result by index without copying"""
        responses = collection.get("responses", [])
        total = len(responses)
        
        if 0 <= index < total:
            text = responses[index]  # Just a reference
            has_more = index < (total - 1)
        else:
            text = ""
            has_more = False
        
        return (text, total, has_more)


# Auto cleanup on module load
memory_tracker.cleanup(force=True)