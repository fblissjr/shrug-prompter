"""
Loop-safe accumulator node for ComfyUI
Designed to accumulate values during ForLoop execution without circular dependencies
"""

import torch
from typing import Tuple, List, Dict, Any

class LoopSafeAccumulator:
    """
    Accumulator designed for use inside ForLoops.
    Maintains state across iterations without creating circular dependencies.
    """

    _accumulators = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # --- THIS IS THE FIX ---
                "item": ("STRING",), # Change from ("*",) to ("STRING",)
                # --- END OF FIX ---
                "loop_id": ("STRING", {"default": "default"}),
                "reset": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "seed": ("INT", {"default": 0}),
            }
        }

    RETURN_TYPES = ("ACCUMULATION",)
    RETURN_NAMES = ("accumulator",)
    FUNCTION = "accumulate"
    CATEGORY = "Shrug Nodes/Core"

    def accumulate(self, item, loop_id="default", reset=False, seed=0):
        """Accumulate items safely during loop execution."""

        key = f"{loop_id}_{seed}"

        if reset or key not in self._accumulators:
            self._accumulators[key] = {"items": [], "metadata": {}}

        self._accumulators[key]["items"].append(item)

        accumulator = {
            "items": self._accumulators[key]["items"].copy(),
            "metadata": self._accumulators[key]["metadata"].copy()
        }

        return (accumulator,)

    @classmethod
    def reset_all(cls):
        cls._accumulators = {}


class LoopAccumulatorReset:
    """
    Resets a LoopSafeAccumulator before loop execution.
    Place this before your ForLoop to ensure clean state.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "loop_id": ("STRING", {"default": "default"}),
                "trigger": ("*",),  # Connect to something that executes before loop
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("reset_done",)
    FUNCTION = "reset"
    CATEGORY = "Shrug Nodes/Core"

    def reset(self, loop_id="default", trigger=None):
        """Reset accumulator for the given loop_id."""
        # Clear the specific accumulator
        keys_to_remove = [k for k in LoopSafeAccumulator._accumulators.keys()
                         if k.startswith(f"{loop_id}_")]
        for key in keys_to_remove:
            del LoopSafeAccumulator._accumulators[key]

        return (True,)
