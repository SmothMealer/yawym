# yawym

Minimal [Hugo](https://gohugo.io/) static site for **https://mechanicalcolor.com/yawym/**.

## Local preview

**Option A — Hugo on your PATH** (e.g. `brew install hugo`):

```bash
hugo server
```

**Option B — same Hugo as CI** (uses `hugo-bin` from this repo):

```bash
npm install
npx hugo server
```

Open the URL Hugo prints (usually `http://localhost:1313/yawym/`).

**Production build (matches Workers CI):**

```bash
npm ci && npm run build
```

## New posts

```bash
hugo new posts/my-topic/index.md
```

Use a **page bundle** (`posts/name/index.md` + images beside it) so images stay next to the post.

---

## GitHub

1. Create a **new repository** on GitHub (empty, no README/license if you already have this repo).
2. From this machine, add the remote and push:

```bash
cd /path/to/yawym
git remote add origin https://github.com/YOUR_USER/yawym.git   # if not already set
git add -A
git commit -m "Add Hugo site scaffold"
git push -u origin main
```

Use your real default branch name (`main` or `master`) in the Cloudflare steps below.

---

## Cloudflare Workers (Wrangler + static assets) — what this repo uses

If you connected the repo as a **Worker** with **static assets**, Cloudflare runs **`npx wrangler deploy`**. Wrangler then runs the **build command** from `wrangler.jsonc` before uploading the `public/` folder.

**Why `npx hugo` failed:** there is no npm package named `hugo` that installs a CLI that way, so npm prints *“could not determine executable to run”*.

**Fix in this repo:** `package.json` includes **`hugo-bin`** (ships the real Hugo binary). The build is:

1. `npm ci` — install `hugo-bin` and `wrangler`
2. `npm run build` — runs `hugo --minify --gc` → writes `public/`

That is configured in **`wrangler.jsonc`** under `build.command`. Commit **`package.json`** and **`package-lock.json`** with the rest of the site.

**Dashboard check:** in the Worker project → **Settings** → **Build**, clear any extra **Build command** that still says `npx hugo` so Wrangler uses the repo’s `wrangler.jsonc` (or set it explicitly to `npm ci && npm run build` if you override there).

**Deploy command** should stay **`npx wrangler deploy`** (or `npm exec wrangler deploy` after `npm ci`).

---

## Cloudflare Pages (build + host)

Cloudflare Pages serves your built site at **`https://<project>.pages.dev`**. Because this site’s `baseURL` is **`/yawym` on mechanicalcolor.com**, you should either:

- **Option A (simplest):** use a **subdomain** like `yawym.mechanicalcolor.com` in Pages (CNAME to Pages), **and** change `hugo.toml` `baseURL` to match; **or**
- **Option B (your URL path):** keep `baseURL` as `https://mechanicalcolor.com/yawym/` and put a **Worker** in front that maps `mechanicalcolor.com/yawym/*` → your `*.pages.dev` site (see below).

These steps assume **Option B** and that **DNS for `mechanicalcolor.com` is on Cloudflare**.

### Create the Pages project

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Select **GitHub**, authorize if needed, pick this repo.
3. **Build settings:**
   - **Framework preset:** None
   - **Build command:**

     ```bash
     hugo --minify --gc
     ```

   - **Build output directory:** `public`
   - **Root directory:** `/` (leave default)
4. **Environment variables** (project → **Settings** → **Environment variables**):
   - **Variable:** `HUGO_VERSION`  
     **Value:** `0.147.6` (or a [current extended](https://github.com/gohugoio/hugo/releases) version; extended only matters if you later use Hugo Pipes SCSS without PostCSS, etc.)

5. Save and deploy. Note the host, e.g. **`yawym.pages.dev`** (yours may differ).

### Preview vs production `baseURL` (optional)

On **`*.pages.dev`**, HTML that references `/yawym/...` will not match files at the Pages **root** (assets 404 on previews). To fix **preview** builds only, you can use a shell build command:

```bash
if [ "$CF_PAGES_BRANCH" = "main" ]; then hugo --minify --gc; else hugo --minify --gc --baseURL "$CF_PAGES_URL/"; fi
```

Change `main` if your production branch is different. Production keeps `hugo.toml` `baseURL` for correct RSS and absolute URLs on **mechanicalcolor.com**.

---

## Cloudflare Worker (serve at `mechanicalcolor.com/yawym`)

Use this when something else (or nothing) already answers `https://mechanicalcolor.com` and you need **only the path** `/yawym` to map to Pages.

1. **Workers & Pages** → **Create** → **Worker** → create worker, e.g. `yawym-proxy`.
2. Replace the script with (set `PAGES_HOST` to your real Pages hostname, e.g. `yawym-xxxxx.pages.dev`):

```javascript
const PAGES_HOST = "yawym-xxxxx.pages.dev"; // no https://

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const prefix = "/yawym";
    if (!url.pathname.startsWith(prefix)) {
      return new Response("Not found", { status: 404 });
    }
    let path = url.pathname.slice(prefix.length);
    if (path === "") path = "/";
    const target = new URL(path + url.search, "https://" + PAGES_HOST);
    const proxied = new Request(target.toString(), request);
    return fetch(proxied);
  },
};
```

3. **Triggers** → **Routes** → **Add route**:
   - Route: `mechanicalcolor.com/yawym*` (or `www.mechanicalcolor.com/yawym*` if you use `www` for the site).
4. If you already have a Worker on `mechanicalcolor.com/*`, merge this logic into that Worker instead of stacking two default routes.

**Important:** If the **apex** already uses another Worker or origin, coordinate routing so `/yawym` is handled by this Worker and the rest unchanged.

### HTTPS and “www”

- Use the **same hostname** in `hugo.toml` `baseURL` as visitors use (`www` vs apex). Mismatch causes duplicate URLs and odd RSS behavior.
- Your certificate on Cloudflare should cover the hostname you use.

---

## Checklist after first deploy

- Open **https://mechanicalcolor.com/yawym/** — home loads, CSS loads.
- Open **https://mechanicalcolor.com/yawym/posts/hello-world/** — sample post and SVG image load.
- Open **https://mechanicalcolor.com/yawym/index.xml** — RSS (for aggregators / future newsletter tooling).

---

## Repo layout

| Path | Role |
|------|------|
| `content/` | Markdown pages; posts under `content/posts/` |
| `content/posts/.../index.md` | Post + co-located images (page bundle) |
| `static/` | Files copied to site root (`static/css/` → `/yawym/css/` when deployed) |
| `layouts/` | HTML templates |
| `hugo.toml` | Site config; **`baseURL` must match public URL** |
| `package.json` / `package-lock.json` | CI: `hugo-bin` + `wrangler`; `npm run build` runs Hugo |
| `wrangler.jsonc` | Workers: static `public/` + `build.command` for Hugo |
| `archetypes/default.md` | Front matter for `hugo new` |
