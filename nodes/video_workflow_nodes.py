"""
Video workflow nodes with automatic memory management.
Designed for frame pair extraction and segment assembly without memory bloat.
"""

import torch
import gc
import weakref
from typing import Tuple, Optional

from .core_vlm_nodes import memory_tracker


class VideoFramePairExtractor:
    """
    Extract frame pairs for video interpolation with zero-copy operations.
    Replaces ImagePairIterator with better memory management.
    """
    
    # Weak cache to avoid keeping tensors in memory
    _cache = weakref.WeakValueDictionary()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "mode": (["sequential_pairs", "all_combinations", "first_to_each"], {"default": "sequential_pairs"}),
                "pair_index": ("INT", {"default": 0, "min": 0}),
            },
            "optional": {
                "stride": ("INT", {"default": 1, "min": 1, "max": 10}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE", "INT", "BOOLEAN", "STRING")
    RETURN_NAMES = ("start_frame", "end_frame", "total_pairs", "has_more", "info")
    FUNCTION = "extract_pair"
    CATEGORY = "VLM/Video"
    
    def extract_pair(self, images, mode="sequential_pairs", pair_index=0, stride=1):
        """Extract frame pairs without copying data"""
        if images.dim() != 4:
            raise ValueError(f"Expected 4D tensor (B,H,W,C), got {images.dim()}D")
        
        batch_size = images.shape[0]
        
        # Calculate pairs based on mode
        if mode == "sequential_pairs":
            # Pairs: (0,1), (1,2), (2,3), etc.
            total_pairs = max(0, (batch_size - 1) // stride)
            start_idx = pair_index * stride
            end_idx = start_idx + stride
            
        elif mode == "all_combinations":
            # All possible pairs: (0,1), (0,2), (0,3), (1,2), (1,3), (2,3)
            total_pairs = (batch_size * (batch_size - 1)) // 2
            # Convert flat index to pair indices
            start_idx = 0
            for i in range(batch_size):
                for j in range(i + 1, batch_size):
                    if pair_index == 0:
                        start_idx, end_idx = i, j
                        break
                    pair_index -= 1
                if start_idx > 0:
                    break
                    
        else:  # first_to_each
            # Pairs: (0,1), (0,2), (0,3), etc.
            total_pairs = batch_size - 1
            start_idx = 0
            end_idx = pair_index + 1
        
        # Validate indices
        if start_idx >= batch_size or end_idx >= batch_size:
            # Return empty frames
            empty = torch.zeros((1,) + images.shape[1:], dtype=images.dtype, device=images.device)
            return (empty, empty, total_pairs, False, f"Index out of range")
        
        # Extract frames using views (no copy)
        start_frame = images[start_idx:start_idx+1]
        end_frame = images[end_idx:end_idx+1]
        
        # Check if more pairs available
        current_pair = pair_index
        has_more = current_pair < (total_pairs - 1)
        
        info = f"Pair {current_pair + 1}/{total_pairs}: frames {start_idx}→{end_idx}"
        
        # Clean up every few iterations
        if pair_index % 5 == 0:
            memory_tracker.cleanup()
        
        return (start_frame, end_frame, total_pairs, has_more, info)


class VideoSegmentAssembler:
    """
    Assemble video segments efficiently without keeping all frames in memory.
    Replaces ImageBatchReassembler with streaming approach.
    """
    
    # Use weak references to allow garbage collection
    _assemblers = weakref.WeakValueDictionary()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "segment": ("IMAGE",),
                "assembler_id": ("STRING", {"default": "default"}),
                "mode": (["accumulate", "streaming", "windowed"], {"default": "streaming"}),
            },
            "optional": {
                "segment_index": ("INT", {"default": -1, "min": -1}),
                "max_frames": ("INT", {"default": 1000, "min": 100, "max": 10000}),
                "window_size": ("INT", {"default": 100, "min": 10, "max": 500}),
                "reset": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "STRING")
    RETURN_NAMES = ("assembled_video", "total_frames", "info")
    FUNCTION = "assemble_segments"
    CATEGORY = "VLM/Video"
    
    def assemble_segments(self, segment, assembler_id="default", mode="streaming", 
                         segment_index=-1, max_frames=1000, window_size=100, reset=False):
        """Assemble video segments with memory management"""
        
        # Register segment for tracking
        memory_tracker.register_tensor(segment)
        
        # Get or create assembler
        if reset or assembler_id not in self._assemblers:
            assembler = {
                "frames": [],
                "frame_count": 0,
                "mode": mode,
                "window_start": 0
            }
            self._assemblers[assembler_id] = assembler
        else:
            assembler = self._assemblers[assembler_id]
        
        # Handle different assembly modes
        if mode == "streaming":
            # Keep only recent frames to avoid memory bloat
            assembled = self._streaming_assembly(segment, assembler, max_frames)
            
        elif mode == "windowed":
            # Sliding window approach
            assembled = self._windowed_assembly(segment, assembler, window_size)
            
        else:  # accumulate
            # Traditional accumulation (use with caution on long videos)
            assembled = self._accumulate_assembly(segment, assembler, max_frames)
        
        total_frames = assembler["frame_count"]
        info = f"Mode: {mode}, Frames: {total_frames}, Memory segments: {len(assembler['frames'])}"
        
        # Cleanup old assemblers
        if len(self._assemblers) > 3:
            oldest_keys = list(self._assemblers.keys())[:-3]
            for key in oldest_keys:
                del self._assemblers[key]
        
        # Force cleanup every 10 segments
        if total_frames % (10 * segment.shape[0]) == 0:
            memory_tracker.cleanup(force=True)
        
        return (assembled, total_frames, info)
    
    def _streaming_assembly(self, segment, assembler, max_frames):
        """Keep only the most recent frames"""
        frames = assembler["frames"]
        
        # Add new segment
        if segment.dim() == 4:
            for i in range(segment.shape[0]):
                frames.append(segment[i:i+1])
                assembler["frame_count"] += 1
        else:
            frames.append(segment)
            assembler["frame_count"] += 1
        
        # Keep only max_frames
        if len(frames) > max_frames:
            # Remove oldest frames
            frames[:] = frames[-max_frames:]
        
        # Concatenate available frames
        if frames:
            return torch.cat(frames, dim=0)
        else:
            return segment
    
    def _windowed_assembly(self, segment, assembler, window_size):
        """Sliding window assembly"""
        frames = assembler["frames"]
        window_start = assembler["window_start"]
        
        # Add to window
        if segment.dim() == 4:
            for i in range(segment.shape[0]):
                frames.append(segment[i:i+1])
                assembler["frame_count"] += 1
        else:
            frames.append(segment)
            assembler["frame_count"] += 1
        
        # Slide window if needed
        if len(frames) > window_size:
            assembler["window_start"] += len(frames) - window_size
            frames[:] = frames[-window_size:]
        
        # Return current window
        if frames:
            return torch.cat(frames, dim=0)
        else:
            return segment
    
    def _accumulate_assembly(self, segment, assembler, max_frames):
        """Traditional accumulation with safety limit"""
        frames = assembler["frames"]
        
        # Check frame limit
        current_count = sum(f.shape[0] for f in frames)
        if current_count >= max_frames:
            # Don't add more frames
            return torch.cat(frames, dim=0) if frames else segment
        
        # Add new segment
        if segment.dim() == 4:
            frames.append(segment)
            assembler["frame_count"] += segment.shape[0]
        else:
            frames.append(segment)
            assembler["frame_count"] += 1
        
        # Periodically consolidate to single tensor to reduce overhead
        if len(frames) > 10:
            consolidated = torch.cat(frames, dim=0)
            frames.clear()
            frames.append(consolidated)
        
        return torch.cat(frames, dim=0) if frames else segment


class SmartImageRangeExtractor:
    """
    Extract image ranges with zero-copy views and automatic cleanup.
    Enhanced version of ImageRangeExtractor.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "start": ("INT", {"default": 0, "min": 0}),
                "count": ("INT", {"default": 1, "min": 1}),
            },
            "optional": {
                "step": ("INT", {"default": 1, "min": 1, "max": 10}),
                "reverse": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "STRING")
    RETURN_NAMES = ("image_range", "actual_count", "info")
    FUNCTION = "extract_range"
    CATEGORY = "VLM/Video"
    
    def extract_range(self, images, start=0, count=1, step=1, reverse=False):
        """Extract range using views to avoid copying"""
        if images.dim() != 4:
            raise ValueError(f"Expected 4D tensor (B,H,W,C), got {images.dim()}D")
        
        batch_size = images.shape[0]
        
        # Calculate indices
        if reverse:
            # Extract from end backwards
            start = batch_size - 1 - start
            indices = list(range(start, max(-1, start - count * step), -step))
        else:
            # Extract forwards
            indices = list(range(start, min(batch_size, start + count * step), step))
        
        if not indices:
            # Return empty tensor
            empty = torch.zeros((0,) + images.shape[1:], dtype=images.dtype, device=images.device)
            return (empty, 0, "No valid indices")
        
        # Use advanced indexing to create view
        image_range = images[indices]
        actual_count = len(indices)
        
        info = f"Extracted {actual_count} frames: indices {indices[0]}...{indices[-1]} (step={step})"
        
        return (image_range, actual_count, info)


class AutoMemoryManager:
    """
    Automatic memory management node that can be inserted anywhere in workflow.
    Provides visual feedback about memory usage.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "trigger": ("*",),  # Any input to trigger cleanup
                "mode": (["gentle", "normal", "aggressive", "nuclear"], {"default": "normal"}),
            },
            "optional": {
                "threshold_mb": ("INT", {"default": 1000, "min": 100, "max": 10000, "step": 100}),
            }
        }
    
    RETURN_TYPES = ("*", "STRING")
    RETURN_NAMES = ("passthrough", "memory_info")
    FUNCTION = "manage_memory"
    CATEGORY = "VLM/Utility"
    
    def manage_memory(self, trigger, mode="normal", threshold_mb=1000):
        """Clean memory based on mode and threshold"""
        import psutil
        import os
        
        # Get current memory usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Determine if cleanup needed
        needs_cleanup = memory_mb > threshold_mb
        
        if needs_cleanup or mode in ["aggressive", "nuclear"]:
            if mode == "gentle":
                gc.collect()
            elif mode == "normal":
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            elif mode == "aggressive":
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                # Force cleanup of tracked objects
                memory_tracker.cleanup(force=True)
            else:  # nuclear
                # Clear everything possible
                gc.collect(2)  # Full collection
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    # Reset memory allocator stats
                    torch.cuda.reset_peak_memory_stats()
                memory_tracker.cleanup(force=True)
                # Force cleanup of module-level caches
                VLMResultCollector._collectors.clear()
                VideoSegmentAssembler._assemblers.clear()
        
        # Get memory after cleanup
        memory_mb_after = process.memory_info().rss / 1024 / 1024
        freed_mb = memory_mb - memory_mb_after
        
        if torch.cuda.is_available():
            gpu_mb = torch.cuda.memory_allocated() / 1024 / 1024
            gpu_info = f", GPU: {gpu_mb:.0f}MB"
        else:
            gpu_info = ""
        
        info = f"Memory: {memory_mb_after:.0f}MB (freed {freed_mb:.0f}MB){gpu_info}"
        
        return (trigger, info)