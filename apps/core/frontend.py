"""
Serves the compiled React storefront (``frontend/dist``) straight from Django.

* Real files inside the build (hashed ``/assets/*``, favicon, ...) are served
  as-is, with long-lived immutable caching for the hashed assets.
* Any other path falls back to ``index.html`` so client-side routes such as
  ``/shop`` or ``/orders/<id>`` survive a hard refresh or a shared link.
* Missing asset-like paths (``/assets/old.js``) are a real 404, never HTML.

For a high-traffic production site, put a CDN or Nginx in front of these
files; this view keeps small deployments to a single container.
"""

import mimetypes
import os
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404, HttpResponse
from django.utils._os import safe_join
from django.views.decorators.http import require_safe

NOT_BUILT_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Storefront not built</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:system-ui,sans-serif;max-width:40rem;margin:12vh auto;padding:0 1rem;
line-height:1.6;color:#1d1814}
code{background:#f3ece0;padding:.1rem .4rem;border-radius:4px}</style></head>
<body><h1>The React storefront hasn't been built yet</h1>
<p>The API is running fine. Build the frontend once so Django can serve it:</p>
<pre><code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></pre>
<p>Or run the live-reloading dev server instead: <code>npm run dev</code> (then open
<code>http://localhost:5173</code>).</p>
<p>API docs: <a href="/api/v1/docs/">/api/v1/docs/</a> &middot; Admin: <a href="/admin/">/admin/</a></p>
</body></html>"""


@require_safe
def serve_frontend(request, path=""):
    dist = Path(settings.FRONTEND_DIST_DIR)
    index = dist / "index.html"
    if not index.is_file():
        return HttpResponse(NOT_BUILT_HTML, status=503, content_type="text/html; charset=utf-8")

    if path:
        try:
            candidate = safe_join(str(dist), path)
        except SuspiciousFileOperation:
            raise Http404("Not found.") from None
        if os.path.isfile(candidate):
            content_type, _ = mimetypes.guess_type(candidate)
            response = FileResponse(open(candidate, "rb"), content_type=content_type or "application/octet-stream")
            if path.startswith("assets/"):
                response["Cache-Control"] = "public, max-age=31536000, immutable"
            return response
        if "." in path.rsplit("/", 1)[-1]:
            raise Http404("Not found.")  # a missing .js/.css/.png must not come back as HTML

    response = FileResponse(open(index, "rb"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-cache"
    return response
