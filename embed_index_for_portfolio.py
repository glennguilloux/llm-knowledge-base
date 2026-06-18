#!/usr/bin/env python3
"""
Unified RAG indexer — builds a single numpy embedding index from:
  1. KB patterns (markdown with YAML frontmatter)
  2. Portfolio apps (HTML with <title>, <meta description>)

Output:
  portfolio_kb_index.npy   — shape (N, 384) float32
  portfolio_kb_meta.json   — list of {id, title, source, language, tags, url, content_preview}

Usage:
  python3 embed_index_for_portfolio.py [--kb-path .] [--portfolio-path /path/to/Applications]
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
import numpy as np
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
SKIP_FILES = {"README.md", "schema.md", "CONTRIBUTING.md", "CHANGELOG.md",
              "RELEASE_CHECKLIST.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md", "LICENSE"}
SKIP_DIRS = {".git", ".venv", "__pycache__", ".github", ".vscode",
             "llm_knowledge_base.egg-info", "templates", ".sisyphus", ".pytest_cache"}


# -- KB pattern parsing ------------------------------------------------

def extract_frontmatter(content: str) -> dict | None:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None


def extract_body(content: str) -> str:
    m = re.match(r"^---\n.*?\n---\n?", content, re.DOTALL)
    return content[m.end():] if m else content


def collect_kb_patterns(kb_path: Path) -> list[dict]:
    entries = []
    for md in sorted(kb_path.rglob("*.md")):
        parts = md.relative_to(kb_path).parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if md.name in SKIP_FILES:
            continue

        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        fm = extract_frontmatter(content)
        if not fm or not fm.get("id"):
            continue

        body = extract_body(content)
        entry_id = fm["id"]
        title = fm.get("title", "")
        language = fm.get("language", "multi")
        category = fm.get("category", "")
        tags = fm.get("tags", [])
        retrieval_hint = fm.get("retrieval_hint", "")
        confidence = fm.get("confidence", "draft")

        embedding_parts = [
            title,
            retrieval_hint,
            " ".join(tags) if isinstance(tags, list) else str(tags),
            language,
            category,
        ]
        embedding_text = " ".join(p for p in embedding_parts if p)
        content_preview = body.strip()[:600]

        # Normalize tags to always be a list
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif not isinstance(tags, list):
            tags = [str(tags)]

        entries.append({
            "id": entry_id,
            "title": title,
            "source": "kb",
            "language": language,
            "category": category,
            "tags": tags,
            "confidence": confidence,
            "retrieval_hint": retrieval_hint,
            "url": "",
            "filepath": str(md.relative_to(kb_path)),
            "embedding_text": embedding_text,
            "content_preview": content_preview,
        })

    return entries


# -- Portfolio app parsing -----------------------------------------------

def collect_portfolio_apps(portfolio_path: Path) -> list[dict]:
    entries = []
    for html in sorted(portfolio_path.glob("*.html")):
        try:
            content = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        soup = BeautifulSoup(content, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else html.stem

        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc.get("content", "") if meta_desc else ""

        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""

        kicker = soup.find(class_=re.compile(r"kicker|app-kicker"))
        kicker_text = kicker.get_text(strip=True) if kicker else ""

        clean_title = re.sub(r"\s*[—–-]\s*Glenn Guilloux\s*$", "", title)
        app_desc = description or h1_text or clean_title
        embedding_text = f"{clean_title} {app_desc} {kicker_text}"
        content_preview = f"{clean_title}: {app_desc}"
        url = f"/Applications/{html.name}"

        entries.append({
            "id": f"app-{html.stem}",
            "title": clean_title,
            "source": "portfolio",
            "language": "",
            "category": "application",
            "tags": [],
            "confidence": "high",
            "url": url,
            "filepath": str(html),
            "embedding_text": embedding_text,
            "content_preview": content_preview,
        })

    return entries


# -- Main ----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build unified RAG index")
    parser.add_argument("--kb-path", type=Path, default=Path("."))
    parser.add_argument("--portfolio-path", type=Path,
                        default=Path("/mnt/apps/BACKUP-RAG/clickandbuilds/glennguilloux/Applications"))
    parser.add_argument("--output-prefix", type=str, default="portfolio_kb")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    print(f"Scanning KB patterns at {args.kb_path} ...")
    kb_entries = collect_kb_patterns(args.kb_path)
    print(f"  Found {len(kb_entries)} KB patterns with frontmatter")

    print(f"Scanning portfolio apps at {args.portfolio_path} ...")
    app_entries = collect_portfolio_apps(args.portfolio_path)
    print(f"  Found {len(app_entries)} portfolio apps")

    all_entries = kb_entries + app_entries
    if not all_entries:
        print("ERROR: No entries found.", file=sys.stderr)
        sys.exit(1)

    print(f"\nTotal entries: {len(all_entries)}")
    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [e["embedding_text"] for e in all_entries]
    print(f"Embedding {len(texts)} entries (batch_size={args.batch_size}) ...")
    embeddings = model.encode(texts, batch_size=args.batch_size,
                              show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)
    print(f"  Embeddings shape: {embeddings.shape}")

    metadata = [{k: v for k, v in e.items() if k != "embedding_text"} for e in all_entries]

    index_path = f"{args.output_prefix}_index.npy"
    meta_path = f"{args.output_prefix}_meta.json"

    np.save(index_path, embeddings)
    print(f"  Saved {index_path} ({embeddings.nbytes / 1024 / 1024:.1f} MB)")

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=1)
    print(f"  Saved {meta_path}")

    kb_count = sum(1 for e in all_entries if e["source"] == "kb")
    app_count = sum(1 for e in all_entries if e["source"] == "portfolio")
    print(f"\nDone! Index: {kb_count} KB + {app_count} portfolio = {len(all_entries)} total, dim={embeddings.shape[1]}")


if __name__ == "__main__":
    main()
