# yawym

Minimal [Hugo](https://gohugo.io/) static site for **https://mechanicalcolor.com/yawym/**.

## Local preview

This site’s production `baseURL` is under **`/yawym/`**. In-page links use that prefix (e.g. **`/yawym/hello-world/`**, **`/yawym/css/...`**). If you start plain `hugo server` and open only **`http://localhost:1313/`** (without `/yawym/`), the home page is not served there, and following links can hit URLs Hugo is not serving—often an empty or broken page in the browser.

**Recommended — same paths as production** (`/yawym/...` links work as-is):

```bash
npm install
npm run dev
```

Then open **`http://localhost:1313/yawym/`** (Hugo prints this URL on startup). The server uses `baseURL` from `hugo.toml` with the port appended.

**Flat URLs on localhost** (home at **`http://localhost:1313/`** only; **`/yawym/`** is not served):

```bash
npm run dev:flat
```

Posts appear at **`/<slug>/...`** for that session only (no `/yawym/` prefix in the path); production `baseURL` in `hugo.toml` is unchanged.

**Option A — Hugo on your PATH** (e.g. `brew install hugo`), flat URLs:

```bash
hugo server -D --port 1313 --bind 127.0.0.1 --appendPort=false --baseURL http://localhost:1313/
```

**Option B — match production paths** (same as `npm run dev`):

```bash
npm install
npx hugo server -D --port 1313 --bind 127.0.0.1
```

Open the URL Hugo prints (with `publishDir` set, that is **`http://localhost:1313/yawym/`**), not the server root alone.

**Previewing a built folder with another static server:** serve the whole **`public/`** directory (Wrangler’s asset root), then open **`http://localhost:<port>/yawym/`**. Do not point the server’s document root at **`public/yawym/`** only: links start with `/yawym/...`, so the browser would request `/yawym/...` from your host and you would need that extra `yawym` segment in the filesystem path.

**Production build (matches Workers CI):**

```bash
npm ci && npm run build
```

## New posts

```bash
hugo new my-topic/index.md
```

Use a **page bundle** (`content/<slug>/index.md` + images beside it) so images stay next to the post. Each post’s front matter should include **`type: post`** (the default archetype sets this) so it appears on the home list and uses the post layout.

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

### Auto-deploy on push to `main`

**Cloudflare does not see your GitHub pushes by default.** Deploys are triggered by **GitHub Actions** (`.github/workflows/deploy.yml`). That job calls **`npx wrangler deploy`**, which needs API credentials stored as **repository secrets**.

#### One-time setup (required)

1. Open your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. **New repository secret** (exact names):

   | Name | Value |
   |------|--------|
   | **`CLOUDFLARE_API_TOKEN`** | Cloudflare → profile icon (top right) → **My Profile** → **API Tokens** → **Create Token** → use template **Edit Cloudflare Workers** (or create a custom token with **Account** → **Workers Scripts** → **Edit** and **Account** → **Workers KV Storage** / **Workers R2** if you add those later). Copy the token once; GitHub stores it as a secret. |
   | **`CLOUDFLARE_ACCOUNT_ID`** | Cloudflare dashboard → **Workers & Pages** → right sidebar **Account ID** (or any zone **Overview** → **Account ID** in the API section). |

3. Confirm **Actions** are allowed: repo **Settings** → **Actions** → **General** → **Actions permissions** → *Allow all actions and reusable workflows* (or your org’s equivalent).

4. Push to **`main`** again, or open **Actions** → **Deploy to Cloudflare Workers** → **Run workflow** → **Run workflow**.

5. Open **Actions** and click the latest run. If it failed, open the job log; if secrets were missing, the first step should now say to add **`CLOUDFLARE_API_TOKEN`** and **`CLOUDFLARE_ACCOUNT_ID`**.

#### Optional: confirm it ran

After a green run, reload **`https://<your-worker>.workers.dev/yawym/`** (or your custom domain) and check that new content appears.

#### If you also use Cloudflare “Connect to Git”

If this repo is **also** connected inside **Cloudflare** for automatic deploys, either **disable** the Cloudflare-side Git build or **remove** this workflow so you do not deploy **twice** on every push.

---

## Custom domain: `mechanicalcolor.com/yawym` (this Worker)

Your preview URL is **`https://<worker>.<subdomain>.workers.dev/yawym/`** (not the workers.dev **root**), because the built files live under `public/yawym/` to match `/yawym/...` links.

On the zone **mechanicalcolor.com** (DNS already on Cloudflare):

1. Open **Workers & Pages** → select the **yawym** worker (the one with static assets).
2. Open **Settings** → **Domains & Routes** (or **Triggers** → **Routes**, depending on dashboard version).
3. Under **Routes**, **Add route**:
   - **`mechanicalcolor.com/yawym*`**  
   If visitors use **`www`**, also add **`www.mechanicalcolor.com/yawym*`** (and keep `hugo.toml` `baseURL` consistent with the hostname you actually use).
4. Save. Cloudflare attaches the route to this worker; HTTPS uses your existing zone certificate.

**If another Worker already handles `mechanicalcolor.com/*`:** the **more specific** route `mechanicalcolor.com/yawym*` should still hit this worker, but if you see the wrong worker, merge routes or adjust order in the dashboard / wrangler `routes` config.

**If the apex is a normal origin (not a Worker) for `/`:** this route only intercepts **`/yawym...`**; the rest of the site is unchanged.

---

## Cloudflare Workers (Wrangler + static assets) — what this repo uses

If you connected the repo as a **Worker** with **static assets**, Cloudflare runs **`npx wrangler deploy`**. Wrangler then runs the **build command** from `wrangler.jsonc` before uploading the `public/` folder (site files are under **`public/yawym/`** after the Hugo build).

**Why `npx hugo` failed:** there is no npm package named `hugo` that installs a CLI that way, so npm prints *“could not determine executable to run”*.

**Fix in this repo:** `package.json` includes **`hugo-bin`** (ships the real Hugo binary). The build is:

1. `npm ci` — install `hugo-bin` and `wrangler`
2. `npm run build` — runs `hugo --minify --gc` → writes the site under **`public/yawym/`** (see `publishDir` in `hugo.toml`) so URL paths like `/yawym/css/...` match the Worker asset tree.

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
- Open **https://mechanicalcolor.com/yawym/hello-world/** — sample post and SVG image load.
- Open **https://mechanicalcolor.com/yawym/index.xml** — RSS (for aggregators / future newsletter tooling).

---

## Repo layout

| Path | Role |
|------|------|
| `content/_index.md` | Home page |
| `content/<slug>/index.md` | Post page bundle (`type: post`); URL is `/yawym/<slug>/` |
| `static/` | Files copied to site root (`static/css/` → `/yawym/css/` when deployed) |
| `layouts/` | HTML templates |
| `hugo.toml` | Site config; **`baseURL` must match public URL**; **`publishDir`** emits `public/yawym/` for subpath hosting |
| `package.json` / `package-lock.json` | CI: `hugo-bin` + `wrangler`; `npm run build` runs Hugo |
| `wrangler.jsonc` | Workers: static `public/` + `build.command` for Hugo |
| `.github/workflows/deploy.yml` | Deploy on push to `main` (needs GitHub Action secrets) |
| `archetypes/default.md` | Front matter for `hugo new` |
