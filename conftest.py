"""Root conftest — prevents pytest from importing __init__.py as a package.

The root __init__.py uses relative imports that only work inside ComfyUI.
Mirrors coderef/ComfyUI-AudioLoopHelper/conftest.py.
"""

collect_ignore = ["__init__.py"]
