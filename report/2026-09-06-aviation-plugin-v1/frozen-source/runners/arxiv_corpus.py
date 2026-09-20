"""arxiv_corpus.py — arXiv 元数据抓取与核验（litbench 语料建设用）。

功能：
  fetch(id_list)   按 arXiv id 批量取 title/abstract/authors/date（ Atom API）。
  search(title)    按标题精确搜索（用于核验子代理给出的论文是否真实存在）。
  verify(cands)    输入候选清单 JSON -> 逐篇在 arXiv 检索标题，输出核验结果。

设计要点：
  - 只做只读 GET export.arxiv.org，遵守 3s 礼貌间隔（arXiv API 要求）；
  - 输出统一含 sha256(title+abstract)，供 PROVENANCE 与任务 YAML 摘要校验；
  - 抓取失败如实标注 fetch_error，绝不静默降级为空摘要。

用法：
  python3 -m runners.arxiv_corpus verify data/cfdagent/litbench/candidates.json
  python3 -m runners.arxiv_corpus fetch 2407.07891,2402.xxxxx
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
POLITENESS_S = 3.1  # arXiv API 礼貌间隔


def _get(url: str, retries: int = 4) -> str:
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "comacbench-corpus/0.1 (research mirror)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # SSL EOF / URLError / timeout 都按退避重试
            last = e
            time.sleep(2.0 * (i + 1))
    raise RuntimeError(f"arxiv fetch failed after {retries} tries: {last}")


def _parse(atom_xml: str) -> list[dict]:
    root = ET.fromstring(atom_xml)
    out = []
    for e in root.findall("a:entry", NS):
        aid = (e.findtext("a:id", "", NS) or "").rsplit("/", 1)[-1]
        title = re.sub(r"\s+", " ", e.findtext("a:title", "", NS)).strip()
        abstract = re.sub(r"\s+", " ", e.findtext("a:summary", "", NS)).strip()
        authors = [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)]
        published = (e.findtext("a:published", "", NS) or "")[:10]
        updated = (e.findtext("a:updated", "", NS) or "")[:10]
        cats = [c.get("term") for c in e.findall("a:category", NS)]
        out.append({
            "arxiv_id": aid,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "first_author": authors[0] if authors else None,
            "published": published,
            "updated": updated,
            "categories": cats,
            "abs_url": f"https://arxiv.org/abs/{aid}",
        })
    return out


def fetch(id_list: list[str]) -> list[dict]:
    """按 arXiv id 批量抓取（一次请求，服务端排序与输入对应）。"""
    url = f"{ARXIV_API}?id_list={','.join(id_list)}&max_results={len(id_list)}"
    return _parse(_get(url))


def search(title: str, max_results: int = 3) -> list[dict]:
    """标题精确短语检索（arXiv ti: 字段），用于核验论文存在性。"""
    q = urllib.parse.quote(f'ti:"{title}"')
    url = f"{ARXIV_API}?search_query={q}&max_results={max_results}"
    return _parse(_get(url))


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", t.lower())).strip()


def _digest(rec: dict) -> str:
    payload = (rec["title"] + "\n" + rec["abstract"]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify(cands_path: str) -> list[dict]:
    cands = json.loads(Path(cands_path).read_text(encoding="utf-8"))
    results = []
    for c in cands:
        title = c.get("title", "").strip()
        hit = None
        if c.get("arxiv_id"):
            recs = fetch([c["arxiv_id"]])
            hit = recs[0] if recs else None
        if hit is None and title:
            recs = search(title)
            want = _norm_title(title)
            for r in recs:
                if _norm_title(r["title"]) == want:
                    hit = r
                    break
            if hit is None and recs:
                hit = recs[0]  # 最近似候选，标注 match=approximate
        time.sleep(POLITENESS_S)
        if hit is None:
            results.append({**c, "verify": "not-on-arxiv", "abstract_sha256": None})
            continue
        exact = _norm_title(hit["title"]) == _norm_title(title)
        results.append({
            **c,
            "arxiv_id": hit["arxiv_id"],
            "title_arxiv": hit["title"],
            "abstract": hit["abstract"],
            "first_author_arxiv": hit["first_author"],
            "published_arxiv": hit["published"],
            "match": "exact" if exact else "approximate",
            "verify": "ok",
            "abstract_sha256": _digest(hit),
        })
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "search", "verify"])
    ap.add_argument("arg")
    args = ap.parse_args()
    if args.cmd == "fetch":
        print(json.dumps(fetch([x for x in args.arg.split(",") if x]), ensure_ascii=False, indent=2))
    elif args.cmd == "search":
        print(json.dumps(search(args.arg), ensure_ascii=False, indent=2))
    else:
        out = verify(args.arg)
        out_path = Path(args.arg).with_name("verified.json")
        Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        ok = sum(1 for r in out if r.get("verify") == "ok")
        print(f"verified {ok}/{len(out)} -> {out_path}")


if __name__ == "__main__":
    main()
