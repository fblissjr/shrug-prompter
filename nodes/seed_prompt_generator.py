# nodes/seed_prompt_generator.py
import sys
import os
import json
import random
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from shrug_router import send_request
except ImportError:
    from ..shrug_router import send_request


class SeedPromptGenerator:
    """
    Creative seed prompt generator that provides starting points for LLM-based
    prompt expansion. Uses various strategies to generate diverse, interesting
    prompts that can be expanded by downstream VLM nodes.
    """
    
    # Predefined seed categories with examples
    SEED_CATEGORIES = {
        "cinematic": {
            "templates": [
                "A {mood} scene featuring {subject} in {location}, {lighting} lighting",
                "{time_of_day} at {location}, {subject} {action}, {cinematography} shot",
                "Close-up of {subject}, {emotion} expression, {color_palette} color grading"
            ],
            "variables": {
                "mood": ["dramatic", "serene", "tense", "melancholic", "euphoric", "mysterious"],
                "subject": ["a lone figure", "two silhouettes", "a crowd", "an empty chair", "a child", "an elderly person"],
                "location": ["abandoned warehouse", "misty forest", "neon-lit street", "vast desert", "foggy pier", "rooftop"],
                "lighting": ["golden hour", "harsh fluorescent", "candlelit", "moonlit", "neon", "stormy"],
                "time_of_day": ["Dawn", "Dusk", "Midnight", "High noon", "Blue hour", "Magic hour"],
                "action": ["walking slowly", "running frantically", "standing still", "looking back", "reaching out", "falling"],
                "cinematography": ["wide angle", "telephoto", "Dutch angle", "bird's eye", "worm's eye", "tracking"],
                "emotion": ["contemplative", "joyful", "fearful", "determined", "lost", "hopeful"],
                "color_palette": ["desaturated", "high contrast", "warm", "cold", "vintage", "cyberpunk"]
            }
        },
        "artistic": {
            "templates": [
                "{art_style} painting of {subject}, {technique} technique, {era} inspired",
                "Abstract representation of {concept}, {color_scheme} palette, {texture} texture",
                "{artist_style} interpretation of {scene}, {medium} on {surface}"
            ],
            "variables": {
                "art_style": ["impressionist", "surrealist", "minimalist", "baroque", "art nouveau", "brutalist"],
                "subject": ["a stormy seascape", "urban decay", "human connection", "solitude", "nature reclaiming", "technology"],
                "technique": ["impasto", "glazing", "pointillist", "sfumato", "chiaroscuro", "collage"],
                "era": ["Renaissance", "Modern", "Contemporary", "Classical", "Romantic", "Post-modern"],
                "concept": ["time", "memory", "dreams", "consciousness", "entropy", "emergence"],
                "color_scheme": ["monochromatic", "complementary", "analogous", "triadic", "split-complementary", "achromatic"],
                "texture": ["smooth", "rough", "layered", "crystalline", "organic", "geometric"],
                "artist_style": ["Van Gogh", "Monet", "Dali", "Picasso", "Hokusai", "Banksy"],
                "medium": ["oil", "watercolor", "digital", "mixed media", "charcoal", "acrylic"],
                "surface": ["canvas", "wood", "metal", "glass", "fabric", "stone"]
            }
        },
        "narrative": {
            "templates": [
                "The moment when {character} discovers {discovery} in {setting}",
                "{time_period}: {character} must {challenge} before {deadline}",
                "A story about {theme} set in {world}, where {twist}"
            ],
            "variables": {
                "character": ["the last survivor", "an AI", "a time traveler", "twin siblings", "a shapeshifter", "the chosen one"],
                "discovery": ["a hidden message", "their true identity", "a portal", "an ancient artifact", "a conspiracy", "their power"],
                "setting": ["a cyberpunk metropolis", "deep space", "Victorian London", "post-apocalyptic wasteland", "underwater city", "parallel dimension"],
                "time_period": ["Year 2150", "Medieval times", "The near future", "Prehistoric era", "Alternate 1960s", "Time loop"],
                "challenge": ["save humanity", "find the truth", "escape the loop", "unite the factions", "prevent the disaster", "remember their past"],
                "deadline": ["the sun explodes", "time runs out", "the portal closes", "memory fades", "the enemy arrives", "reality collapses"],
                "theme": ["redemption", "identity", "sacrifice", "power", "love", "survival"],
                "world": ["a world without color", "Earth's last city", "digital consciousness", "fractured timeline", "merged realities", "the afterlife"],
                "twist": ["nothing is real", "everyone is connected", "the hero is the villain", "time moves backwards", "death is temporary", "memories can be traded"]
            }
        },
        "conceptual": {
            "templates": [
                "Visual metaphor for {abstract_concept} using {concrete_element}",
                "The intersection of {concept1} and {concept2}, represented through {medium}",
                "If {hypothesis}, visualized as {visualization}"
            ],
            "variables": {
                "abstract_concept": ["infinity", "consciousness", "entropy", "emergence", "synchronicity", "paradox"],
                "concrete_element": ["flowing water", "broken mirrors", "tangled threads", "growing crystals", "burning pages", "melting clocks"],
                "concept1": ["technology", "nature", "time", "memory", "reality", "identity"],
                "concept2": ["humanity", "chaos", "order", "dreams", "mathematics", "emotion"],
                "medium": ["particle simulation", "organic growth", "geometric patterns", "data visualization", "light installation", "sound waves"],
                "hypothesis": ["thoughts had color", "time was visible", "emotions were tangible", "memories were places", "words were alive", "music had shape"],
                "visualization": ["a living map", "breathing architecture", "liquid geometry", "crystallized sound", "woven light", "sculpted time"]
            }
        },
        "experimental": {
            "templates": [
                "{impossible_scenario} but {unusual_constraint}",
                "Documenting {phenomenon} through {unconventional_method}",
                "{material} {transformation} into {unexpected_result}"
            ],
            "variables": {
                "impossible_scenario": ["gravity reverses", "colors have sound", "shadows are solid", "time flows sideways", "thoughts are visible", "silence is loud"],
                "unusual_constraint": ["only in mirrors", "during dreams", "through music", "in negative space", "between heartbeats", "at light speed"],
                "phenomenon": ["collective consciousness", "quantum emotions", "temporal echoes", "dimensional bleeding", "memory storms", "reality glitches"],
                "unconventional_method": ["taste mapping", "emotional frequency", "dream photography", "thought printing", "time-lapse sculpture", "sound painting"],
                "material": ["Light", "Sound", "Time", "Memory", "Emotion", "Data"],
                "transformation": ["crystallizes", "liquefies", "fragments", "multiplies", "inverts", "evolves"],
                "unexpected_result": ["living architecture", "temporal fabric", "emotional landscape", "consciousness map", "reality mesh", "existence pattern"]
            }
        }
    }
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "category": (["all", "cinematic", "artistic", "narrative", "conceptual", "experimental", "custom"], {
                    "default": "all",
                    "tooltip": "Category of seed prompts to generate"
                }),
                "count": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 100,
                    "tooltip": "Number of seed prompts to generate"
                }),
                "variation_mode": (["random", "systematic", "evolutionary", "thematic"], {
                    "default": "random",
                    "tooltip": "How to vary the prompts: random, systematic progression, evolutionary (each builds on previous), or thematic (variations on a theme)"
                }),
                "complexity": (["simple", "moderate", "complex"], {
                    "default": "moderate",
                    "tooltip": "Complexity level of generated prompts"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "tooltip": "Random seed for reproducible results (-1 for random)"
                }),
            },
            "optional": {
                "custom_templates": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Custom templates (one per line). Use {variable} for placeholders"
                }),
                "custom_variables": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Custom variables as JSON dict: {\"variable\": [\"option1\", \"option2\"]}"
                }),
                "context": ("VLM_CONTEXT", {"tooltip": "Optional VLM context for AI-enhanced generation"}),
                "base_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Base prompt that all seeds will build upon"
                }),
                "avoid_terms": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated terms to avoid in generation"
                }),
                "prefer_terms": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated terms to prefer in generation"
                }),
                "enable_ai_enhancement": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Use AI to enhance and expand seed prompts"
                }),
                "enhancement_instruction": ("STRING", {
                    "multiline": True,
                    "default": "Enhance this seed prompt with more detail and atmosphere while keeping the core concept:",
                    "tooltip": "Instruction for AI enhancement"
                }),
            }
        }
    
    RETURN_TYPES = ("LIST", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("seed_prompts", "first_prompt", "all_prompts_text", "prompt_count", "generation_info")
    FUNCTION = "generate_seeds"
    CATEGORY = "Shrug Nodes/Creative"
    
    def generate_seeds(self, category="all", count=5, variation_mode="random", complexity="moderate",
                      seed=-1, custom_templates="", custom_variables="", context=None,
                      base_prompt="", avoid_terms="", prefer_terms="", enable_ai_enhancement=False,
                      enhancement_instruction=""):
        """Generate creative seed prompts based on specified parameters."""
        
        # Set random seed if specified
        if seed >= 0:
            random.seed(seed)
        else:
            # Use current time for true randomness
            random.seed(int(datetime.now().timestamp() * 1000000) % 2147483647)
        
        # Parse avoid and prefer terms
        avoid_list = [term.strip().lower() for term in avoid_terms.split(",") if term.strip()]
        prefer_list = [term.strip() for term in prefer_terms.split(",") if term.strip()]
        
        # Prepare templates and variables
        templates, variables = self._prepare_templates_and_variables(
            category, custom_templates, custom_variables
        )
        
        # Generate base seeds
        if variation_mode == "random":
            seeds = self._generate_random_seeds(templates, variables, count, complexity)
        elif variation_mode == "systematic":
            seeds = self._generate_systematic_seeds(templates, variables, count, complexity)
        elif variation_mode == "evolutionary":
            seeds = self._generate_evolutionary_seeds(templates, variables, count, complexity)
        else:  # thematic
            seeds = self._generate_thematic_seeds(templates, variables, count, complexity)
        
        # Apply base prompt if provided
        if base_prompt:
            seeds = [f"{base_prompt} {seed}" for seed in seeds]
        
        # Filter based on avoid terms
        if avoid_list:
            seeds = [s for s in seeds if not any(term in s.lower() for term in avoid_list)]
            # Regenerate if we filtered too many
            while len(seeds) < count:
                new_seed = self._generate_single_seed(templates, variables, complexity)
                if not any(term in new_seed.lower() for term in avoid_list):
                    seeds.append(new_seed)
        
        # Prefer certain terms by reordering
        if prefer_list:
            def preference_score(prompt):
                return sum(1 for term in prefer_list if term.lower() in prompt.lower())
            seeds.sort(key=preference_score, reverse=True)
        
        # Enhance with AI if requested
        if enable_ai_enhancement and context:
            seeds = self._enhance_seeds_with_ai(seeds, context, enhancement_instruction)
        
        # Ensure we have exactly the requested count
        seeds = seeds[:count]
        
        # Generate metadata
        generation_info = self._generate_info(category, variation_mode, complexity, len(seeds), seed)
        
        # Format outputs
        first_prompt = seeds[0] if seeds else ""
        all_prompts_text = "\n\n".join(seeds)
        
        return (seeds, first_prompt, all_prompts_text, len(seeds), generation_info)
    
    def _prepare_templates_and_variables(self, category, custom_templates, custom_variables):
        """Prepare templates and variables based on category and custom inputs."""
        templates = []
        variables = {}
        
        # Add category templates
        if category == "all":
            for cat_data in self.SEED_CATEGORIES.values():
                templates.extend(cat_data["templates"])
                variables.update(cat_data["variables"])
        elif category in self.SEED_CATEGORIES:
            cat_data = self.SEED_CATEGORIES[category]
            templates = cat_data["templates"].copy()
            variables = cat_data["variables"].copy()
        
        # Add custom templates
        if custom_templates:
            custom_temps = [t.strip() for t in custom_templates.split("\n") if t.strip()]
            templates.extend(custom_temps)
        
        # Add custom variables
        if custom_variables:
            try:
                custom_vars = json.loads(custom_variables)
                variables.update(custom_vars)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse custom variables JSON")
        
        # Ensure we have templates
        if not templates:
            templates = ["A {subject} in {location}"]
            variables = {
                "subject": ["person", "animal", "object", "landscape"],
                "location": ["forest", "city", "space", "underwater"]
            }
        
        return templates, variables
    
    def _generate_single_seed(self, templates, variables, complexity):
        """Generate a single seed prompt."""
        template = random.choice(templates)
        
        # Find all variables in template
        import re
        var_pattern = r'\{(\w+)\}'
        found_vars = re.findall(var_pattern, template)
        
        # Replace variables
        result = template
        for var in found_vars:
            if var in variables:
                value = random.choice(variables[var])
                result = result.replace(f"{{{var}}}", value)
        
        # Add complexity
        if complexity == "complex":
            # Add additional descriptive elements
            additions = [
                f", {random.choice(['featuring', 'with', 'including'])} {random.choice(['intricate', 'detailed', 'complex'])} {random.choice(['patterns', 'textures', 'compositions'])}",
                f", {random.choice(['dramatic', 'subtle', 'dynamic'])} {random.choice(['lighting', 'shadows', 'contrast'])}",
                f", {random.choice(['rich', 'muted', 'vibrant'])} {random.choice(['colors', 'tones', 'palette'])}"
            ]
            result += random.choice(additions)
        elif complexity == "simple":
            # Simplify by removing some descriptors
            result = re.sub(r',\s*\w+\s+(lighting|shot|technique)', '', result)
        
        return result
    
    def _generate_random_seeds(self, templates, variables, count, complexity):
        """Generate random seed prompts."""
        return [self._generate_single_seed(templates, variables, complexity) for _ in range(count)]
    
    def _generate_systematic_seeds(self, templates, variables, count, complexity):
        """Generate systematic variations cycling through options."""
        seeds = []
        template_idx = 0
        var_indices = {var: 0 for var in variables}
        
        for i in range(count):
            template = templates[template_idx % len(templates)]
            
            # Systematic replacement
            import re
            var_pattern = r'\{(\w+)\}'
            found_vars = re.findall(var_pattern, template)
            
            result = template
            for var in found_vars:
                if var in variables:
                    options = variables[var]
                    value = options[var_indices[var] % len(options)]
                    result = result.replace(f"{{{var}}}", value)
                    var_indices[var] += 1
            
            seeds.append(result)
            template_idx += 1
        
        return seeds
    
    def _generate_evolutionary_seeds(self, templates, variables, count, complexity):
        """Generate seeds where each builds on the previous."""
        seeds = []
        base_seed = self._generate_single_seed(templates, variables, complexity)
        seeds.append(base_seed)
        
        evolution_patterns = [
            "Later, {evolution}",
            "Transformed into {evolution}",
            "Evolving to show {evolution}",
            "Progressing towards {evolution}",
            "Shifting to reveal {evolution}"
        ]
        
        evolutions = [
            "a different perspective", "increased intensity", "subtle changes",
            "dramatic transformation", "unexpected elements", "deeper meaning"
        ]
        
        for i in range(1, count):
            pattern = random.choice(evolution_patterns)
            evolution = random.choice(evolutions)
            evolved = f"{seeds[-1]}. {pattern.format(evolution=evolution)}"
            seeds.append(evolved)
        
        return seeds
    
    def _generate_thematic_seeds(self, templates, variables, count, complexity):
        """Generate variations on a central theme."""
        # Choose a theme
        theme_template = random.choice(templates)
        theme_vars = {}
        
        # Extract variables from theme
        import re
        var_pattern = r'\{(\w+)\}'
        found_vars = re.findall(var_pattern, theme_template)
        
        # Lock some variables for consistency
        for var in found_vars:
            if var in variables and random.random() < 0.5:  # 50% chance to lock
                theme_vars[var] = random.choice(variables[var])
        
        seeds = []
        for i in range(count):
            result = theme_template
            for var in found_vars:
                if var in theme_vars:
                    value = theme_vars[var]  # Use locked value
                elif var in variables:
                    value = random.choice(variables[var])  # Random value
                else:
                    value = var  # Keep as is
                result = result.replace(f"{{{var}}}", value)
            seeds.append(result)
        
        return seeds
    
    def _enhance_seeds_with_ai(self, seeds, context, instruction):
        """Use AI to enhance and expand seed prompts."""
        enhanced = []
        
        for seed in seeds:
            try:
                # Build enhancement request
                messages = [
                    {"role": "system", "content": "You are a creative prompt enhancer. Enhance prompts with rich detail while preserving their core concept."},
                    {"role": "user", "content": f"{instruction}\n\n{seed}"}
                ]
                
                # Get provider config from context
                provider_config = context.get("provider_config", {})
                
                response = send_request(
                    provider=provider_config["provider"],
                    messages=messages,
                    api_key=provider_config["api_key"],
                    base_url=provider_config["base_url"],
                    llm_model=provider_config["llm_model"],
                    max_tokens=200,
                    temperature=0.8,
                    top_p=0.9,
                    timeout=30
                )
                
                if "choices" in response and response["choices"]:
                    enhanced_text = response["choices"][0]["message"]["content"].strip()
                    enhanced.append(enhanced_text)
                else:
                    enhanced.append(seed)  # Fallback to original
                    
            except Exception as e:
                print(f"Enhancement failed for seed: {e}")
                enhanced.append(seed)  # Fallback to original
        
        return enhanced
    
    def _generate_info(self, category, mode, complexity, count, seed):
        """Generate information about the seed generation."""
        info = []
        info.append(f"Generated {count} seed prompts")
        info.append(f"Category: {category}")
        info.append(f"Variation mode: {mode}")
        info.append(f"Complexity: {complexity}")
        if seed >= 0:
            info.append(f"Seed: {seed}")
        else:
            info.append("Seed: random")
        
        return "\n".join(info)