#!/usr/bin/env python3
"""Regenerate edges.json from papers.json using the Semantic Scholar graph API.

Run this after adding a paper:  python3 tools/build_graph.py
The site does not call the API at runtime - the edges are committed.
"""
import json, re, sys, time, urllib.request
from itertools import combinations

ARXIV = re.compile(r"arxiv\.org/abs/(\d+\.\d+)")
COUPLING_MIN = 3  # shared references needed to draw a coupling edge

def arxiv_id(url):
    m = ARXIV.search(url or "")
    return m.group(1) if m else None

def collect(papers):
    """arXiv id -> node, for presented papers and the references they cite."""
    nodes = {}
    for p in papers:
        for entry, kind in [(p, "paper")] + [(r, "reference") for r in p.get("references", [])]:
            aid = arxiv_id(entry.get("url"))
            if aid and aid not in nodes:
                nodes[aid] = {"id": aid, "title": entry["title"],
                              "url": entry["url"], "kind": kind}
                if kind == "paper":
                    nodes[aid]["date"] = p["date"]  # lets the page mark it upcoming
    return nodes

def previous_counts():
    """Citation counts from the last run, used if the API refuses this one."""
    try:
        old = json.load(open("edges.json"))
    except Exception:
        return {}
    return {n["id"]: n["citations"] for n in old.get("nodes", []) if n.get("citations")}

def citation_counts(aids):
    """One batch call for how often each paper has been cited.

    The API rate-limits aggressively, so retry with backoff. A miss must never
    silently become a zero - every node would then render at minimum size.
    """
    req = urllib.request.Request(
        "https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount",
        data=json.dumps({"ids": ["arXiv:" + a for a in aids]}).encode(),
        headers={"Content-Type": "application/json"})
    for attempt, wait in enumerate([15, 45, 90, 0]):
        try:
            rows = json.load(urllib.request.urlopen(req, timeout=60))
            got = {a: (row or {}).get("citationCount") for a, row in zip(aids, rows)}
            if any(v is not None for v in got.values()):
                return got
        except Exception as exc:
            print("citation batch attempt %d failed (%s)" % (attempt + 1, exc), file=sys.stderr)
        if wait:
            print("retrying in %ds" % wait, file=sys.stderr)
            time.sleep(wait)
    return {}

def references_of(aid):
    url = ("https://api.semanticscholar.org/graph/v1/paper/arXiv:%s"
           "/references?fields=externalIds&limit=500" % aid)
    data = json.load(urllib.request.urlopen(url, timeout=30))
    out = set()
    for item in data.get("data", []):
        ext = (item.get("citedPaper") or {}).get("externalIds") or {}
        if ext.get("ArXiv"):
            out.add(ext["ArXiv"].split("v")[0])
    return out

def main():
    papers = json.load(open("papers.json"))
    nodes = collect(papers)
    fresh, kept = citation_counts(list(nodes)), previous_counts()
    missing = []
    for aid in nodes:
        count = fresh.get(aid)
        if count is None:
            count = kept.get(aid)          # fall back to the last good value
            if count is None:
                missing.append(aid)
                count = 0
            else:
                print("%s: kept previous count %d" % (aid, count), file=sys.stderr)
        nodes[aid]["citations"] = count
    if missing:
        print("WARNING: no citation count for %s - they will render at minimum size"
              % ", ".join(missing), file=sys.stderr)

    refs = {}
    for aid in nodes:
        try:
            refs[aid] = references_of(aid)
            print("%s: %d refs" % (aid, len(refs[aid])), file=sys.stderr)
        except Exception as exc:
            print("%s: failed (%s)" % (aid, exc), file=sys.stderr)
            refs[aid] = set()
        time.sleep(1.2)  # unauthenticated rate limit

    edges, cited = [], set()
    for a in nodes:
        for b in nodes:
            if a != b and b in refs.get(a, ()):
                edges.append({"a": a, "b": b, "kind": "cites"})
                cited.add(frozenset((a, b)))
    for a, b in combinations(nodes, 2):
        if frozenset((a, b)) in cited:
            continue  # a real citation already connects these two
        shared = len(refs.get(a, set()) & refs.get(b, set()))
        if shared >= COUPLING_MIN:
            edges.append({"a": a, "b": b, "kind": "shares", "weight": shared})

    graph = {"nodes": sorted(nodes.values(), key=lambda n: n["id"]), "edges": edges}
    with open("edges.json", "w") as fh:
        json.dump(graph, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("%d nodes, %d edges -> edges.json" % (len(nodes), len(edges)), file=sys.stderr)

main()
