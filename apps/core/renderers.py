from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """
    Wraps every successful JSON response in a predictable envelope:

        {"success": true, "message": "...", "data": ..., "meta": {...}}

    Errors are already shaped by ``apps.core.exceptions.api_exception_handler``
    (``{"success": false, "message": ..., "errors": {...}, "code": ...}``).
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response is None or response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)
        if isinstance(data, dict) and "success" in data:  # already enveloped
            return super().render(data, accepted_media_type, renderer_context)

        envelope = {"success": True, "message": getattr(response, "message", "Success.")}
        if isinstance(data, dict) and set(data) == {"results", "meta"}:  # paginated
            envelope["data"] = data["results"]
            envelope["meta"] = data["meta"]
        else:
            envelope["data"] = data
        return super().render(envelope, accepted_media_type, renderer_context)
