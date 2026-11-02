# open-webui-subpath

Custom Open WebUI image patched to serve correctly behind a reverse-proxy
subpath (`/webui`). Upstream has no official support for this.

Used by `manifests/open-webui/deployment.yaml`
(`registry:5000/open-webui-subpath:v0.12.5`).

## What the patch does

- `Dockerfile` — adds `ARG WEBUI_SUBPATH` and bakes it into the frontend build.
- `src/lib/constants.ts`, `vite.config.ts` — `WEBUI_BASE_URL` derives from the
  build-time `WEBUI_SUBPATH`, which feeds every frontend API/asset URL.
- `svelte.config.js` — `kit.paths.base` set to the same subpath, so
  SvelteKit's own routing/`%sveltekit.assets%` resolve correctly.
- `src/app.html` — hardcoded `/static/...` and `/manifest.json` links
  (favicons, splash screen) prefixed via `%sveltekit.assets%`.
- `src/routes/+layout.svelte` — the socket.io client's `path` option is
  hardcoded and overrides the URL argument, so it needs the subpath too.
- `backend/open_webui/main.py` — wraps the fully-configured app under
  `WEBUI_SUBPATH` (read at runtime) via `outer.mount(subpath, inner)`. The
  outer app must reuse the inner app's `lifespan` *and* share its `.state`
  object directly — hundreds of `app.state.X = ...` assignments run at
  import time against the original app object, before this wrap happens.
- `backend/open_webui/socket/main.py` — `socketio_path` is hardcoded
  absolute (`/ws/socket.io`). Starlette's `Mount` never rewrites
  `scope['path']` (only accumulates `root_path`), so the engine.io ASGI
  driver matches against the literal request path, which now carries the
  subpath prefix too.
- `patch-sveltekit.cjs` (run from the Dockerfile right after `npm ci`,
  against `node_modules/@sveltejs/kit`) — Open WebUI's own frontend source
  has ~150 call sites written as plain root-relative strings:
  `goto('/admin')`, `<a href="/admin">`, etc. Per the URL spec, resolving a
  string starting with `/` against a base URL always discards the base's
  own path, so every one of those silently drops the `/webui` prefix and
  SvelteKit's router then treats the navigation as "external" (different
  pathname than `base` expects) and does a full browser navigation to the
  wrong, unprefixed URL — this is what produced the `/error` 401/500 dead
  end. Patching every call site isn't practical or maintainable, so this
  patches SvelteKit's own shared chokepoint instead (`resolve_url` and
  `get_link_info` in `node_modules/@sveltejs/kit/src/runtime/client/utils.js`)
  so every call site is fixed at once. No-ops when no base/subpath is
  configured. The script hard-fails the build if its target strings aren't
  found verbatim, as a tripwire for a future `@sveltejs/kit` version bump.

## Rebuilding for a new upstream version

```bash
WEBUI_TAG=v0.X.Y ./build.sh
```

The patch may need manual adjustment if upstream restructures any of the
patched files — re-apply with `git apply --reject` to see what still fits,
then update `patch/webui-subpath.patch` from the resulting diff.
