"""shrug-prompter: ComfyUI nodes for heylookitsanllm.

Probes for the ComfyUI V3 extension API and, if present, exposes
`comfy_entrypoint` for node registration and registers a `/shrug/get_models`
HTTP route that proxies the server's `/v1/models` endpoint to the JS widget.
"""

try:
    from comfy_api.latest import ComfyExtension  # noqa: F401 — probe only
except ImportError:
    pass
else:
    from .nodes import comfy_entrypoint  # noqa: F401

    def _register_model_route() -> None:
        try:
            import comfy.server
            from aiohttp import web
        except ImportError:
            return

        server = getattr(comfy.server, "PromptServer", None)
        instance = getattr(server, "instance", None) if server else None
        if instance is None:
            return

        from .client import ShrugClient

        async def get_models_handler(request):
            base_url = request.query.get("base_url", "").strip()
            api_key = request.query.get("api_key", "").strip() or None
            if not base_url:
                return web.json_response(
                    {"success": False, "error": "base_url required"}, status=400
                )
            try:
                client = ShrugClient(base_url=base_url, api_key=api_key, timeout=10.0)
                models = await client.models()
                vision_first = sorted(
                    ({"id": m.id, "vision": m.vision} for m in models),
                    key=lambda m: (not m["vision"], m["id"]),
                )
                return web.json_response({"success": True, "models": vision_first})
            except Exception as e:
                return web.json_response(
                    {"success": False, "error": str(e)}, status=500
                )

        instance.app.add_routes([web.get("/shrug/get_models", get_models_handler)])

    _register_model_route()


WEB_DIRECTORY = "web"
__all__ = ["WEB_DIRECTORY"]
