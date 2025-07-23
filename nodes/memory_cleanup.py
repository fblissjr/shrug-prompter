"""
Global memory cleanup node for shrug-prompter.
Provides centralized cleanup of all caches and accumulators.
"""

import gc
import torch


class GlobalMemoryCleanup:
    """
    Node to clear all caches and accumulators across shrug-prompter nodes.
    Place this node before heavy operations to ensure clean memory state.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "trigger": ("*",),  # Any input to trigger execution
            },
            "optional": {
                "cleanup_mode": (["light", "normal", "aggressive", "nuclear"], {
                    "default": "normal",
                    "tooltip": "light=caches only, normal=caches+accumulators, aggressive=+gc, nuclear=+cuda cache"
                }),
                "verbose": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("*", "STRING")
    RETURN_NAMES = ("trigger_pass", "cleanup_report")
    FUNCTION = "cleanup_memory"
    CATEGORY = "Shrug Nodes/Memory"
    
    def cleanup_memory(self, trigger, cleanup_mode="normal", verbose=True):
        """Clean up memory across all shrug-prompter nodes"""
        report_lines = []
        total_freed = 0
        
        try:
            # Import all nodes that have caches/accumulators
            from .prompter import ShrugPrompter
            from .loop_compatible_nodes import LoopAwareVLMAccumulator
            from .core_vlm_nodes import VLMResultCollector
            
            # Light cleanup - just caches
            if cleanup_mode in ["light", "normal", "aggressive", "nuclear"]:
                # Clear ShrugPrompter caches
                prompter_count = 0
                for obj in gc.get_objects():
                    if isinstance(obj, ShrugPrompter):
                        cache_size = len(obj._cache)
                        obj._cache.clear()
                        obj._cache_hits = 0
                        obj._cache_misses = 0
                        prompter_count += 1
                        total_freed += cache_size
                        if verbose and cache_size > 0:
                            report_lines.append(f"Cleared {cache_size} entries from ShrugPrompter cache")
                
                if prompter_count > 0:
                    report_lines.append(f"Cleaned {prompter_count} ShrugPrompter instances")
            
            # Normal cleanup - caches + accumulators
            if cleanup_mode in ["normal", "aggressive", "nuclear"]:
                # Clear LoopAwareVLMAccumulator
                if hasattr(LoopAwareVLMAccumulator, '_accumulators'):
                    acc_count = len(LoopAwareVLMAccumulator._accumulators)
                    LoopAwareVLMAccumulator._accumulators.clear()
                    if acc_count > 0:
                        report_lines.append(f"Cleared {acc_count} VLM accumulators")
                        total_freed += acc_count
                
                # Clear VLMResultCollector instances
                collector_count = 0
                for obj in gc.get_objects():
                    if isinstance(obj, VLMResultCollector):
                        coll_size = len(obj._collectors)
                        obj._collectors.clear()
                        collector_count += 1
                        total_freed += coll_size
                        if verbose and coll_size > 0:
                            report_lines.append(f"Cleared {coll_size} result collectors")
                
                if collector_count > 0:
                    report_lines.append(f"Cleaned {collector_count} VLMResultCollector instances")
            
            # Aggressive cleanup - run garbage collection
            if cleanup_mode in ["aggressive", "nuclear"]:
                collected = gc.collect()
                if collected > 0:
                    report_lines.append(f"Garbage collected {collected} objects")
            
            # Nuclear cleanup - clear CUDA cache
            if cleanup_mode == "nuclear" and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                report_lines.append("Cleared CUDA cache")
                
                # Report CUDA memory stats
                allocated = torch.cuda.memory_allocated() / 1024**3
                reserved = torch.cuda.memory_reserved() / 1024**3
                report_lines.append(f"CUDA memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
            
            # Summary
            if not report_lines:
                report_lines.append("No memory to clean up")
            else:
                report_lines.insert(0, f"=== Memory Cleanup Report ({cleanup_mode} mode) ===")
                report_lines.append(f"Total items freed: {total_freed}")
                
        except Exception as e:
            report_lines.append(f"Error during cleanup: {str(e)}")
        
        cleanup_report = "\n".join(report_lines)
        if verbose:
            print(cleanup_report)
        
        return (trigger, cleanup_report)


# For backward compatibility
class MemoryCleanupNode(GlobalMemoryCleanup):
    """Alias for GlobalMemoryCleanup"""
    pass