#!/usr/bin/env python3
"""Generate an image with Cloudflare Workers AI.

Usage: gen.py MODEL OUTFILE "PROMPT" [WIDTH HEIGHT]
Reads CF_ACCOUNT and CF_TOKEN from the environment.
"""
import base64
import json
import os
import sys
import urllib.request
import uuid


def call(model, prompt, width, height):
    account = os.environ["CF_ACCOUNT"]
    token = os.environ["CF_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {token}"}

    if "flux-2" in model:
        # FLUX.2 models take multipart form data
        boundary = uuid.uuid4().hex
        fields = {"prompt": prompt, "width": str(width), "height": str(height)}
        if "dev" in model:
            fields["steps"] = "28"
        body = b""
        for k, v in fields.items():
            body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        payload = {"prompt": prompt}
        if "schnell" in model:
            payload["steps"] = 8
        else:
            payload.update({"width": width, "height": height})
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if ctype.startswith("image/"):
        return data
    d = json.loads(data)
    if not d.get("success", True) and d.get("errors"):
        raise SystemExit(f"API error: {d['errors']}")
    res = d.get("result", d)
    img = res.get("image") if isinstance(res, dict) else None
    if not img:
        raise SystemExit(f"No image in response: {str(d)[:500]}")
    return base64.b64decode(img)


if __name__ == "__main__":
    model, out, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
    w = int(sys.argv[4]) if len(sys.argv) > 4 else 864
    h = int(sys.argv[5]) if len(sys.argv) > 5 else 1536
    try:
        img = call(model, prompt, w, h)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:800]}")
    with open(out, "wb") as f:
        f.write(img)
    print(out, len(img))
