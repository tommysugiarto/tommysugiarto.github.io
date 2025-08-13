#!/usr/bin/env python3
import json, sys
from datetime import datetime
from pathlib import Path
try:
    from scholarly import scholarly
except Exception as e:
    print("ERROR: scholarly not available:", e, file=sys.stderr)
    sys.exit(1)

SCHOLAR_ID = "oPSq5PQAAAAJ"
MAX_PUBS = 50

def main():
    author = scholarly.search_author_id(SCHOLAR_ID)
    filled = scholarly.fill(author, sections=['publications'])
    pubs_out = []
    for p in filled.get('publications', [])[:MAX_PUBS]:
        try:
            bib = scholarly.fill(p)['bib']
            pubs_out.append({
                "title": bib.get("title"),
                "authors": [a.strip() for a in (bib.get("author") or "").split(" and ") if a.strip()],
                "year": int(bib.get("pub_year")) if bib.get("pub_year") else None,
                "venue": bib.get("venue"),
                "url": p.get("eprint_url") or p.get("pub_url") or p.get("citedby_url")
            })
        except Exception:
            continue
    pubs_out.sort(key=lambda x: (x["year"] or 0), reverse=True)
    Path("publications.json").write_text(json.dumps(pubs_out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(pubs_out)} publications")

if __name__ == "__main__":
    main()
