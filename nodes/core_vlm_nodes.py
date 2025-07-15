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
    _tensors = weakref.WeakSet()
    _arrays = weakref.WeakSet()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_tensor(self, tensor):
        """Register a tensor for tracking"""
        self._tensors.add(tensor)
    
    def register_array(self, array):
        """Register a numpy array for tracking"""
        self._arrays.add(array)
    
    def cleanup(self, force=False):
        """Clean up unused memory"""
        # Clear dead references
        self._tensors = weakref.WeakSet(t for t in self._tensors if t is not None)
        self._arrays = weakref.WeakSet(a for a in self._arrays if a is not None)
        
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
            },
            "optional": {
                "context": ("VLM_CONTEXT",),
                "seed": ("INT", {"default": -1}),
            }
        }
    
    RETURN_TYPES = ("VLM_RESULTS",)
    RETURN_NAMES = ("results",)
    FUNCTION = "process_images"
    CATEGORY = "VLM/Core"
    
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()
    
    def process_images(self, images, system_prompt, user_prompt, max_tokens, temperature, context=None, seed=-1):
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
                "model": context.get("llm_model", "unknown"),
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
                        max_tokens, temperature, context, seed
                    )
                    results["responses"].append(response)
                    
                    # Clean up after each image
                    if i % 3 == 0:
                        memory_tracker.cleanup()
            else:
                # Single image
                response = self._process_single_image(
                    images, system_prompt, user_prompt,
                    max_tokens, temperature, context, seed
                )
                results["responses"].append(response)
        
        finally:
            # Always clean up, even if error occurs
            memory_tracker.cleanup(force=True)
        
        return (results,)
    
    def _process_single_image(self, image_tensor, system_prompt, user_prompt, max_tokens, temperature, context, seed):
        """Process a single image efficiently"""
        # Convert to base64 without keeping intermediate copies
        with torch.no_grad():
            # Move to CPU if needed, but don't copy
            if image_tensor.is_cuda:
                image_tensor = image_tensor.cpu()
            
            # Convert to numpy without copy if possible
            image_np = image_tensor.squeeze(0).numpy()
            
            # Convert to PIL Image
            image_np = (image_np * 255).astype(np.uint8)
            pil_image = Image.fromarray(image_np)
            
            # Encode to base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format="JPEG", quality=85, optimize=True)
            img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            
            # Free the numpy array immediately
            del image_np
            del pil_image
        
        # Make API call
        try:
            from ..shrug_router import send_request
        except ImportError:
            from shrug_router import send_request
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]}
        ]
        
        kwargs = {
            "provider": context["provider"],
            "base_url": context["base_url"],
            "api_key": context["api_key"],
            "llm_model": context["llm_model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed if seed >= 0 else None
        }
        
        try:
            response = send_request(**kwargs)
            # Extract just the text content, don't keep the full response
            if isinstance(response, dict) and "choices" in response:
                return response["choices"][0]["message"]["content"]
            return str(response)
        finally:
            # Clean up the base64 string
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
        
        # Process based on mode
        if mode == "both":
            # Need both versions - process efficiently
            processed = self._process_for_vlm(images.clone(), target_size, jpeg_quality)
            original = images
        elif mode == "optimize_for_vlm":
            processed = self._process_for_vlm(images, target_size, jpeg_quality)
            original = images
        else:  # prepare_for_video
            processed = self._process_for_video(images)
            original = images
        
        count = images.shape[0] if images.dim() == 4 else 1
        
        # Clean up
        memory_tracker.cleanup()
        
        return (processed, original, count)
    
    def _process_for_vlm(self, images, target_size, jpeg_quality):
        """Optimize images for VLM processing"""
        if target_size is None:
            return images
        
        # Process in-place when possible
        B, H, W, C = images.shape
        
        # Calculate new dimensions
        if H > W:
            new_h = target_size
            new_w = int(W * target_size / H)
        else:
            new_w = target_size
            new_h = int(H * target_size / W)
        
        # Resize efficiently
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
            images = images[:, :new_h, :new_w, :]
        
        return images


class VLMResultCollector:
    """
    Efficient result collector that doesn't duplicate data.
    Uses weak references to avoid keeping results in memory unnecessarily.
    """
    
    _collectors = weakref.WeakValueDictionary()
    
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