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
- `src/routes/+layout.svelte` — two separate socket.io bugs:
  - the client's `path` option is hardcoded and overrides the URL
    argument, so it needs the subpath too.
  - **the actual cause of "chat doesn't update live, only after a reload"**:
    `io(WEBUI_BASE_URL, {...})` passed the subpath as socket.io-client's
    first argument, which it treats as a *namespace* to connect under
    (same-origin bare-path form), not an origin/path prefix — see
    [socket.io's docs on same-origin namespaces](https://socket.io/docs/v4/client-initialization/).
    The transport-level engine.io handshake still succeeds either way (so
    it *looks* connected), but `backend/open_webui/socket/main.py` never
    passes `namespace=` to any `@sio.on(...)` / `sio.emit(...)` call — every
    handler is bound to the default `"/"` namespace. A client connected
    under `/webui` therefore never receives a single app-level event
    (search-status updates, streamed tokens, anything) even though the
    socket shows as connected. The final answer still saves correctly
    (that part doesn't go through the socket), so reloading — which
    re-fetches the chat over plain REST — always "fixes" it, which is
    what made this so easy to misdiagnose as a caching or timing issue.
    Fix: pass `undefined` as the connection URL (default namespace,
    same-origin) and let `path` alone carry the subpath.
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
- ~18 components had an `onerror` handler on an `<img>` falling back to a
  hardcoded `/favicon.png` or `/user.png` (model avatars, user avatars,
  citation icons). Same root-relative problem as above, but for images
  rather than navigation — these don't go through SvelteKit's router at
  all, so the `patch-sveltekit.cjs` fix doesn't cover them. Worse than the
  navigation bug: an unprefixed fallback 401s behind the gateway, its
  `onerror` fires again, and since the handler unconditionally reassigned
  the same broken URL, this looped indefinitely — observed in production
  as 5000+ failed requests in a few seconds, pegging the main thread and
  making the whole page look hung (reported as "chat doesn't show the
  response until I reload"). Fixed by prefixing with `WEBUI_BASE_URL` and
  clearing `onerror` before reassigning, so a still-broken fallback fails
  once instead of looping. `backend/open_webui/main.py`'s
  `get_manifest_json` (PWA install icons) and `swagger_ui_html` had the
  same hardcoded-path problem server-side; prefixed with `WEBUI_SUBPATH`
  the same way as the other backend routes.

## Rebuilding for a new upstream version

```bash
WEBUI_TAG=v0.X.Y ./build.sh
```

The patch may need manual adjustment if upstream restructures any of the
patched files — re-apply with `git apply --reject` to see what still fits,
then update `patch/webui-subpath.patch` from the resulting diff.
