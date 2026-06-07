"""
chunks.py — Milestone 3: Chunking stage

Reads the flattened thread records in raw_data/ (produced by ingest.py) and
splits each thread's text into overlapping chunks for embedding.

Chunking strategy (see planning.md):
    - Target size:  800 - 1,200 characters
    - Overlap:      ~200 characters
    - Boundaries:   snapped to comment / line breaks wherever possible so a
                    chunk never cuts through the middle of a comment. Lines are
                    the atomic unit; only a single line that is itself longer
                    than the max is hard-split (on sentence/word boundaries).

Output: chunks.json — a flat JSON array of chunk records, ready for the
embedding stage (Milestone 4) to loop over.

Usage:
    python chunks.py
"""

import glob
import json
import os

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

INPUT_DIR = "raw_data"
OUTPUT_FILE = "chunks.json"

MIN_CHARS = 800
MAX_CHARS = 1200
OVERLAP_CHARS = 200

# Boundaries we prefer when forced to hard-split a single oversized line,
# in order of preference (most natural break first).
SENTENCE_SEPARATORS = (". ", "! ", "? ", "; ", ", ", " ")


# --------------------------------------------------------------------------- #
# Splitting helpers
# --------------------------------------------------------------------------- #

def hard_split_line(line, max_chars):
    """Split a single line that exceeds max_chars into smaller pieces.

    Snaps each cut back to the nearest sentence/word boundary in the second
    half of the window so we don't slice mid-word; falls back to a hard cut
    only if no boundary is found.
    """
    pieces = []
    remaining = line.strip()
    while len(remaining) > max_chars:
        window = remaining[:max_chars]
        cut = max_chars
        for sep in SENTENCE_SEPARATORS:
            idx = window.rfind(sep)
            # Only snap if the boundary is reasonably deep into the window,
            # otherwise we'd produce a tiny piece and waste space.
            if idx >= max_chars // 2:
                cut = idx + len(sep)
                break
        pieces.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def build_units(content, max_chars):
    """Break flattened content into atomic units (one per non-empty line).

    Any line longer than max_chars is pre-split via hard_split_line so that
    every returned unit is guaranteed to fit inside a single chunk.
    """
    units = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) <= max_chars:
            units.append(line)
        else:
            units.extend(hard_split_line(line, max_chars))
    return units


def joined_len(units):
    """Length of units joined by newlines (matches how chunks are emitted)."""
    if not units:
        return 0
    return sum(len(u) for u in units) + (len(units) - 1)


def overlap_tail(units, overlap_chars):
    """Return the trailing whole units totalling up to ~overlap_chars.

    Snapping the overlap to whole lines (rather than a raw character count)
    keeps the carried-over context as complete comments. If the single last
    unit is already longer than overlap_chars it is still returned whole.
    """
    tail = []
    length = 0
    for unit in reversed(units):
        added = len(unit) + (1 if tail else 0)
        if tail and length + added > overlap_chars:
            break
        tail.insert(0, unit)
        length += added
    return tail


# --------------------------------------------------------------------------- #
# Core chunking
# --------------------------------------------------------------------------- #

def chunk_units(units, min_chars, max_chars, overlap_chars):
    """Greedily pack units into chunks of <= max_chars with line-level overlap.

    A chunk is flushed when adding the next unit would exceed max_chars. The
    next chunk is then seeded with the previous chunk's trailing units (the
    overlap), unless doing so wouldn't leave room for the next unit.
    """
    chunks = []
    current = []
    cur_len = 0

    for unit in units:
        sep = 1 if current else 0
        if current and cur_len + sep + len(unit) > max_chars:
            chunks.append("\n".join(current))

            tail = overlap_tail(current, overlap_chars)
            tail_len = joined_len(tail)
            # Only carry the overlap forward if the next unit still fits after
            # it; otherwise start the new chunk fresh (the unit is large enough
            # to stand on its own).
            if tail and tail_len + 1 + len(unit) <= max_chars:
                current = list(tail)
                cur_len = tail_len
            else:
                current = []
                cur_len = 0
            sep = 1 if current else 0

        current.append(unit)
        cur_len += sep + len(unit)

    if current:
        chunks.append("\n".join(current))

    return chunks


def chunk_document(record):
    """Turn one raw_data record into a list of chunk dicts."""
    units = build_units(record["flattened_content"], MAX_CHARS)
    texts = chunk_units(units, MIN_CHARS, MAX_CHARS, OVERLAP_CHARS)

    chunks = []
    for i, text in enumerate(texts):
        chunks.append({
            "post_title": record.get("post_title", ""),
            "source_url": record.get("source_url", ""),
            "chunk_index": i,
            "char_count": len(text),
            "text": text,
        })
    return chunks


# --------------------------------------------------------------------------- #
# Verification reporting
# --------------------------------------------------------------------------- #

def measured_overlap(chunk_a, chunk_b):
    """Length of the longest suffix of chunk_a that is a prefix of chunk_b.

    Used only for the verification report, to confirm consecutive chunks
    actually share carried-over text.
    """
    a, b = chunk_a["text"], chunk_b["text"]
    limit = min(len(a), len(b))
    for size in range(limit, 0, -1):
        if a[-size:] == b[:size]:
            return size
    return 0


def print_report(all_chunks):
    """Print stats so the chunk sizes / overlaps can be eyeballed against spec."""
    counts = [c["char_count"] for c in all_chunks]
    below = sum(1 for n in counts if n < MIN_CHARS)
    above = sum(1 for n in counts if n > MAX_CHARS)

    print("\n--- Verification ---")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Char count  : min {min(counts)}, max {max(counts)}, "
          f"avg {round(sum(counts) / len(counts))}")
    print(f"In 800-1200 : {len(counts) - below - above}/{len(counts)} "
          f"({below} under min, {above} over max)")

    # Show overlap between the first two chunks of the same thread, if any.
    for i in range(len(all_chunks) - 1):
        a, b = all_chunks[i], all_chunks[i + 1]
        if a["source_url"] == b["source_url"]:
            ov = measured_overlap(a, b)
            print(f"Sample overlap (chunks {a['chunk_index']}->{b['chunk_index']} "
                  f"of '{a['post_title'][:30]}...'): {ov} chars")
            break


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def main():
    paths = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    if not paths:
        print(f"No records found in {INPUT_DIR}/. Run ingest.py first.")
        return

    all_chunks = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        doc_chunks = chunk_document(record)
        all_chunks.extend(doc_chunks)
        print(f"{os.path.basename(path):<16} -> {len(doc_chunks):>3} chunks")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        json.dump(all_chunks, handle, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_chunks)} chunks to {OUTPUT_FILE}")
    print_report(all_chunks)


if __name__ == "__main__":
    main()
