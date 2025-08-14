#!/usr/bin/env python3
import json, sys, time, random, traceback
from pathlib import Path

# pip: scholarly==1.7.11
from scholarly import scholarly, ProxyGenerator

SCHOLAR_ID = "oPSq5PQAAAAJ"   # your profile id
MAX_PUBS = 50                  # limit how much we fetch
MAX_ATTEMPTS = 6               # total retries (with backoff)

def setup_proxy():
    """
    Try to rotate free proxies to reduce Google Scholar blocking.
    If it fails, continue without a proxy.
    """
    try:
        pg = ProxyGenerator()
        # Try a few times to get free proxies
        if pg.FreeProxies():
            scholarly.use_proxy(pg)
            print("Proxy enabled via FreeProxies()", flush=True)
        else:
            print("No free proxies available; continuing without proxy", flush=True)
    except Exception as e:
        print(f"Proxy setup failed: {e}", flush=True)

def fetch_once():
    """One fetch attempt. Returns list of publications (possibly empty)."""
    author = scholarly.search_author_id(SCHOLAR_ID)
    filled = scholarly.fill(author, sections=['publications'])
    pubs_out = []
    for p in filled.get('publications', [])[:MAX_PUBS]:
        try:
            # Gentle delay between item fetches
            time.sleep(0.6 + random.random() * 0.4)
            bib = scholarly.fill(p)['bib']
            pubs_out.append({
                "title": bib.get("title"),
                "authors": [a.strip() for a in (bib.get("author") or "").split(" and ") if a.strip()],
                "year": int(bib.get("pub_year")) if bib.get("pub_year") else None,
                "venue": bib.get("venue"),
                "url": p.get("eprint_url") or p.get("pub_url") or p.get("citedby_url")
            })
        except Exception as e:
            # Skip problematic entries but keep going
            print(f"Warn: failed to parse one item: {e}", flush=True)
            continue
    # Sort newest first
    pubs_out.sort(key=lambda x: (x["year"] or 0), reverse=True)
    return pubs_out

def main():
    setup_proxy()

    backoff = 5  # seconds
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt}/{MAX_ATTEMPTS}…", flush=True)
            pubs = fetch_once()
            # Write even if empty (so the site shows a graceful message)
            Path("publications.json").write_text(
                json.dumps(pubs, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"OK: wrote {len(pubs)} publications to publications.json", flush=True)
            return
        except Exception as e:
            print("ERROR during fetch:", e, flush=True)
            traceback.print_exc()
            if attempt < MAX_ATTEMPTS:
                sleep_s = backoff + random.randint(0, 6)
                print(f"Retrying in {sleep_s}s…", flush=True)
                time.sleep(sleep_s)
                backoff = min(backoff * 2, 60)  # cap growth
            else:
                # Final failure should exit 1 so the job fails loudly
                sys.exit(1)

if __name__ == "__main__":
    main()
