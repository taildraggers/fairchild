"""Scraper for Fairchild listings on barnstormers.com.

Barnstormers' single-manufacturer category pages (the same pattern seen in
the companion Aviat, CubCrafters, de Havilland, Maule, Van's RV, RANS,
Luscombe, Just Aircraft, Kitfox, Bellanca, Stearman, Waco, Pitts,
Taylorcraft, Swift, Beechcraft, and Air Tractor repos) can mix in off-brand
or off-topic listings with no distinguishing HTML markup from the genuine
ones. So results are filtered by title against a small allowlist of
Fairchild-specific terms before being published.

Fairchild used a notoriously varied model-designation system across
decades - the Model 24 line alone spans dozens of suffix combinations
(24C8, 24C8C, 24CR, 24R, 24R-46 "Argus", 24W, 24H, 24K, 24J, 24G, etc.)
covering different engines and eras, plus the wartime PT-19/PT-23/PT-26
"Cornell" primary trainer family, the earlier Model 22 open-cockpit
trainer, the M-62 (PT-19's original factory designation), and the
UC-61 "Forwarder" (export/lend-lease Model 24). Rather than try to
enumerate every historical variant - a losing battle, the same one faced
in the companion Waco repo - a recognized code is trusted when present
(gated behind the "Fairchild" brand word, since bare model numbers like
"24" or "22" are far too generic-looking to trust standalone), but a bare
mention of "Fairchild" with no specific code stated is enough on its own
to publish too, since plenty of genuine listings just say "Fairchild 24"
or "Fairchild Cornell" without stating an exact sub-variant.

Titles that read as parts, accessories, services, or raffles are still
dropped regardless. Surviving titles are rewritten to a canonical "YEAR
FAIRCHILD MODEL" form when the ad states a model year and a specific
model, "YEAR Fairchild" when only the model is missing, "FAIRCHILD MODEL"
when only the year is missing, or plain "Fairchild" when neither is
stated.

Gear note: every Fairchild model covered by this category (the Model 22,
Model 24, and PT-19/23/26 Cornell lines) is a pre-WWII-era design with
fixed conventional tailwheel gear by default and no tricycle-gear variant
ever built - tricycle gear didn't become common in general aviation until
well after these designs were established. So no categorical gear
exclusion is needed here, unlike the companion Beechcraft repo's Model 18.
The standard text-based tricycle/nosewheel safety net is still applied to
every listing as a general precaution.
"""
from __future__ import annotations

import re
from urllib.parse import quote, unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from .common import (
    Listing,
    extract_date,
    extract_location,
    extract_price,
    fetch,
    format_aircraft_title,
)

SITE_NAME = "Barnstormers.com"
BASE = "https://www.barnstormers.com"
MAKE = "Fairchild"

# Category page for Fairchild listings on Barnstormers.
CATEGORY_URLS = [
    f"{BASE}/category-16476-Antique-Classic--Fairchild.html",
]

MAX_PAGES = 10
LISTING_LINK_RE = re.compile(r"^/classified-(\d+)-(.+)\.html$")
GENERIC_SITE_TITLE_SNIPPET = "barnstormers.com find aircraft"


def _compact(text: str) -> str:
    return re.sub(r"[\s-]", "", text.lower())


# "Fairchild" is the only coarse-gate phrase used - the model codes below
# carry too much substring-collision risk (bare "24" or "22" could match
# all sorts of unrelated numbers) to use safely as a coarse filter on
# their own.
TARGET_MODEL_PHRASES = ["fairchild"]


def _matches_target_models(title: str) -> bool:
    compact = _compact(title)
    return any(phrase in compact for phrase in TARGET_MODEL_PHRASES)


_BRAND_RE = re.compile(r"\bfairchild\b", re.IGNORECASE)

_PT_RE = re.compile(r"\bpt[\s-]?(19|23|26)[\s-]?([a-z])?\b", re.IGNORECASE)
_CORNELL_RE = re.compile(r"\bcornell\b", re.IGNORECASE)
_UC61_RE = re.compile(r"\buc[\s-]?61\b", re.IGNORECASE)
_M62_RE = re.compile(r"\bm[\s-]?62\b", re.IGNORECASE)
# Model 24: "24" plus an alphanumeric suffix (24R, 24W, 24C8, 24C8C,
# 24CR, 24CRC, 24R-46, etc.).
_MODEL24_RE = re.compile(r"\b24[\s-]?([a-z]{1,2}\d{0,2}(?:[\s-]?\d{1,2})?[a-z]{0,1})\b", re.IGNORECASE)
# Model 22: "22" plus an optional short suffix (22C7, 22C7A, 22C7B, 22C7C).
_MODEL22_RE = re.compile(r"\b22[\s-]?([a-z]\d{0,2}[a-z]{0,1})?\b", re.IGNORECASE)


def _extract_model(title: str) -> tuple[str, str] | None:
    if not _BRAND_RE.search(title):
        return None

    match = _PT_RE.search(title)
    if match:
        number, suffix = match.groups()
        return MAKE, f"PT-{number}{suffix.upper()}" if suffix else f"PT-{number}"

    if _UC61_RE.search(title):
        return MAKE, "UC-61"
    if _M62_RE.search(title):
        return MAKE, "M-62"

    match = _MODEL24_RE.search(title)
    if match:
        suffix = match.group(1)
        suffix = re.sub(r"[\s-]", "", suffix) if suffix else ""
        return MAKE, f"24{suffix.upper()}" if suffix else "24"

    match = _MODEL22_RE.search(title)
    if match:
        suffix = match.group(1)
        return MAKE, f"22{suffix.upper()}" if suffix else "22"

    if _CORNELL_RE.search(title):
        return MAKE, "Cornell"

    return MAKE, ""


# Ads whose title or body text explicitly calls out tricycle/nosewheel gear
# are dropped, regardless of which model they are - see module docstring.
_NON_TAILWHEEL_KEYWORDS = (
    "tricycle gear",
    "tricycle landing gear",
    "trike gear",
    "tri-gear",
    "tri gear",
    "nosewheel",
    "nose wheel",
    "nose-wheel",
)


def _is_non_tailwheel(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _NON_TAILWHEEL_KEYWORDS)


def _page_url(category_url: str, page: int) -> str:
    """Build a category page's URL directly.

    Barnstormers' category pager renders as page-number buttons with no
    "Next" text or rel="next" attribute for a link-following heuristic to
    find (confirmed on the companion Van's RV, Aviat, and several other
    repos, where that approach silently stopped after page 1) - so each
    page's URL is built from the known
    ?seocategory=<url-encoded-path>&page=<n> pattern instead.
    """
    if page <= 1:
        return category_url
    path = urlparse(category_url).path
    return f"{category_url}?seocategory={quote(path, safe='')}&page={page}"


def _title_from_url(url: str) -> str:
    """Listing pages share a generic <title>/<h1>, but the URL slug is the ad's own title."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    match = LISTING_LINK_RE.match("/" + slug)
    if not match:
        return unquote(slug)
    return unquote(match.group(2)).replace("-", " ").strip()


def _find_listing_links(html: str) -> set[str]:
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0]
        if LISTING_LINK_RE.match(href):
            links.add(urljoin(BASE, href))
    return links


def _debug_dump_hrefs(html: str, limit: int = 25) -> None:
    soup = BeautifulSoup(html, "lxml")
    hrefs = [a["href"] for a in soup.find_all("a", href=True)]
    interesting = [h for h in hrefs if "classified" in h.lower() or "fairchild" in h.lower()]
    sample = interesting[:limit] or hrefs[:limit]
    print(f"  [debug] {len(hrefs)} total <a href> on page; sample: {sample}")


def _parse_detail_page(url: str, html: str) -> Listing | None:
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    if title:
        title = re.sub(r"\s*[\|\-]\s*Barnstormers.*$", "", title, flags=re.IGNORECASE).strip()
    if not title or GENERIC_SITE_TITLE_SNIPPET in title.lower():
        title = _title_from_url(url)
    if not title:
        return None

    if not _matches_target_models(title):
        return None

    text = soup.get_text(" ", strip=True)

    if _is_non_tailwheel(title) or _is_non_tailwheel(text):
        return None

    formatted_title = format_aircraft_title(title, text, _extract_model)
    if not formatted_title:
        return None
    # A bare-"Fairchild" match (no specific model code) leaves a trailing
    # space from format_aircraft_title's "{make} {model}" join, since
    # _extract_model returns an empty model string in that case.
    title = formatted_title.rstrip()

    price = extract_price(text)
    location = extract_location(text)
    date_posted = extract_date(text)

    return Listing(
        title=title,
        price=price,
        location=location,
        date_posted=date_posted,
        site=SITE_NAME,
        url=url,
    )


def scrape() -> list[Listing]:
    print(f"[{SITE_NAME}] starting scrape")
    all_links: set[str] = set()

    for category_url in CATEGORY_URLS:
        seen_this_category: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            url = _page_url(category_url, page)
            html = fetch(url)
            if not html:
                break
            links = _find_listing_links(html)
            new_links = links - seen_this_category
            print(f"  [{category_url}] page {page}: {len(links)} links ({len(new_links)} new)")
            if page == 1 and not links:
                _debug_dump_hrefs(html)
            seen_this_category |= links
            if not new_links:
                break
        all_links |= seen_this_category

    print(f"[{SITE_NAME}] {len(all_links)} unique listing URLs found")

    candidate_links = {url for url in all_links if _matches_target_models(_title_from_url(url))}
    print(f"[{SITE_NAME}] {len(candidate_links)} match Fairchild product names")

    listings: list[Listing] = []
    for url in sorted(candidate_links):
        html = fetch(url)
        if not html:
            continue
        listing = _parse_detail_page(url, html)
        if listing:
            listings.append(listing)

    print(f"[{SITE_NAME}] parsed {len(listings)} listings")
    return listings
