# Fairchild

Daily aggregator of Fairchild classified listings (Model 24 and its many
suffix variants, Model 22, and the PT-19/PT-23/PT-26 "Cornell" wartime
trainer family) from [Barnstormers.com](https://www.barnstormers.com),
published as a static page (`docs/index.html`) meant to be embedded via
`<iframe>` on taildraggers.com.

Controller.com was evaluated (in the companion [Aeronca](https://github.com/taildraggers/aeronca)
repo) and dropped: its search results are only reachable through an internal
client-side widget (not a plain URL), which a headless browser can't drive
reliably for an unattended daily job.

Note: in the companion [Aviat](https://github.com/taildraggers/aviat),
[CubCrafters](https://github.com/taildraggers/cub-crafters),
[de Havilland](https://github.com/taildraggers/de-Havilland),
[Maule](https://github.com/taildraggers/maule),
[Van's RV](https://github.com/taildraggers/vans),
[RANS](https://github.com/taildraggers/rans),
[Luscombe](https://github.com/taildraggers/luscombe),
[Just Aircraft](https://github.com/taildraggers/just-aircraft),
[Kitfox](https://github.com/taildraggers/kitfox),
[Bellanca](https://github.com/taildraggers/bellanca),
[Stearman](https://github.com/taildraggers/stearman),
[Waco](https://github.com/taildraggers/waco),
[Pitts](https://github.com/taildraggers/pitts),
[Taylorcraft](https://github.com/taildraggers/taylorcraft),
[Swift](https://github.com/taildraggers/swift),
[Beechcraft](https://github.com/taildraggers/beech), and
[Air Tractor](https://github.com/taildraggers/airtractor) repos,
Barnstormers' single-manufacturer category pages turned out to include
unrelated listings mixed in with no distinguishing HTML markup. This repo
is built with the same fix from day one: `scraper/barnstormers.py`
filters by title against a small allowlist (see `TARGET_MODEL_PHRASES` in
`scraper/barnstormers.py`) before publishing.

Fairchild used a notoriously varied model-designation system across
decades - the Model 24 line alone spans dozens of suffix combinations
(`24C8`, `24C8C`, `24CR`, `24R`, `24R-46` "Argus", `24W`, `24H`, `24K`,
`24J`, `24G`, etc.) covering different engines and eras, plus the wartime
`PT-19`/`PT-23`/`PT-26` "Cornell" primary trainer family, the earlier
Model 22 open-cockpit trainer, the `M-62` (PT-19's original factory
designation), and the `UC-61` "Forwarder" (export/lend-lease Model 24).
Rather than try to enumerate every historical variant - a losing battle,
the same one faced in the companion Waco repo - a recognized code is
trusted when present (gated behind the "Fairchild" brand word, since bare
model numbers like `24` or `22` are far too generic-looking to trust
standalone), but a bare mention of "Fairchild" with no specific code
stated is enough on its own to publish too, since plenty of genuine
listings just say "Fairchild 24" or "Fairchild Cornell" without stating an
exact sub-variant. Titles that read as parts, accessories, services, or
raffles are still dropped regardless. Every surviving listing's title is
rewritten to a canonical **`YEAR FAIRCHILD MODEL`** form when the ad
states a model year and a specific model (e.g. `1943 Fairchild PT-19`),
`YEAR Fairchild` when only the model is missing, `FAIRCHILD MODEL` when
only the year is missing, or plain **`Fairchild`** when neither is stated.

**Gear note:** every Fairchild model covered by this category (the Model
22, Model 24, and PT-19/23/26 Cornell lines) is a pre-WWII-era design with
fixed conventional tailwheel gear by default and no tricycle-gear variant
ever built - tricycle gear didn't become common in general aviation until
well after these designs were established. So no categorical gear
exclusion is needed here, unlike the companion
[Beechcraft](https://github.com/taildraggers/beech) repo's Model 18. The
standard text-based tricycle/nosewheel safety net used in the companion
repos is still applied to every listing as a general precaution.

## How it works

- `scraper/barnstormers.py` searches Barnstormers.com's Fairchild category
  for listings, follows pagination, then keeps only the ones whose URL
  slug matches the Fairchild allowlist (Barnstormers builds each
  listing's URL slug directly from the ad's own title, so this runs
  before any detail page is fetched). For the matches, it visits each
  listing's detail page to pull out the price, location, and posted date
  (falling back to regex heuristics over the visible text since the site
  doesn't expose structured data). The title is derived from the listing
  URL's own SEO slug, since every detail page shares one generic
  `<title>`/`<h1>`; the final parsed title is checked against the
  allowlist again as a safety net. Pagination is built directly from
  Barnstormers' known `?seocategory=<url-encoded-path>&page=<n>` URL
  pattern rather than discovered by following a "Next" link, since this
  category's pager renders as page-number buttons with no "Next" text or
  `rel="next"` attribute to find (a lesson learned the hard way in the
  companion Van's RV and Aviat repos, where the link-following approach
  silently stopped after page 1).
- `main.py` runs the scraper, de-duplicates results, sorts them
  newest-posted-first, and renders them into `docs/index.html` titled
  **"Other Fairchild Ads on the Web"**, with one row per listing: Title
  (linked to the original ad), Price, Location, Date Posted, and Site
  Posted On. Below phone width, each row collapses into a card (title +
  price on one line, location/date/site on a smaller line below) instead
  of a horizontally-scrolling table. Below the table, a "Search More
  Fairchild Listings" section links out to Trade-A-Plane, Controller, and
  ASO - sites that block automated scraping, but are still worth sending
  visitors to directly via a pre-filled search. Links use
  `rel="noopener noreferrer"` and the page sets a `no-referrer` meta
  policy, so none of these sites see that the click came from
  taildraggers.com.
- `.github/workflows/daily-scrape.yml` runs the whole thing once a day (13:00 UTC),
  commits the regenerated `docs/index.html` if it changed, and can also be triggered
  manually from the Actions tab (`workflow_dispatch`).

## One-time setup: enable GitHub Pages

This repo publishes `docs/index.html` as a plain static file — GitHub Pages just needs
to be pointed at it once:

1. Go to **Settings → Pages** in this repository.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. Branch: `main`, folder: `/docs`. Save.
4. GitHub will publish the page at `https://taildraggers.github.io/fairchild/`
   (may take a minute or two the first time).

Also check **Settings → Actions → General**:
- **Actions permissions**: "Allow all actions and reusable workflows".
- **Workflow permissions**: "Read and write permissions" (needed so the daily
  job can commit the regenerated page back to the repo).

## Embedding on taildraggers.com

```html
<iframe
  src="https://taildraggers.github.io/fairchild/"
  title="Other Fairchild Ads on the Web"
  style="width: 100%; height: 800px; border: 0;"
  loading="lazy">
</iframe>
```

The page also posts its rendered height to the parent window on load/resize
(`{ type: "taildraggers:resize", height }`) so it can be auto-sized instead
of using a fixed guessed height - add a matching `message` listener on the
embedding page to pick this up.

## Running locally

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
python main.py
```

This writes/overwrites `docs/index.html`.

## Notes

- If Barnstormers changes its markup or is briefly unreachable, the run logs will
  show a `[warn]`/`[error]` line pointing at what broke rather than failing silently.
- The scraper identifies itself with a browser-like `User-Agent` and adds a short
  delay between requests to be polite to the site.
- Only one Barnstormers category is currently configured
  (`category-16476-Antique-Classic--Fairchild.html`). If listings turn out
  to be split across additional categories, add more URLs to
  `CATEGORY_URLS` in `scraper/barnstormers.py`.
- The Model 24/22 suffix regex isn't exhaustive of every Fairchild variant
  ever built. Missing a code isn't fatal since the bare-"Fairchild"
  fallback still publishes the listing (just without a specific model in
  the title) - but if a particular code turns up often enough to be worth
  naming explicitly, add it to `scraper/barnstormers.py`.
