"""
ingest.py — Milestone 3: Ingestion and Chunking (parse + flatten stage)

Reads the raw Reddit thread JSON dumps in documents/json_dumps/ (saved manually
from a logged-in browser, since Reddit blocks anonymous .json requests),
flattens each thread (parent post + recursive comment tree) into a single
conversational text stream, strips system noise, and writes one clean JSON file
per thread into raw_data/.

Each dump is the standard Reddit thread structure: a 2-element list where
index [0] is the parent-post listing and index [1] is the comment-tree listing.

Usage:
    python ingest.py
"""

import glob
import json
import os

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

INPUT_DIR = os.path.join("documents", "json_dumps")
OUTPUT_DIR = "raw_data"

# Comments we never want in the flattened stream.
NOISE_AUTHORS = {"AutoModerator"}
NOISE_BODIES = {"[deleted]", "[removed]"}


# --------------------------------------------------------------------------- #
# Parsing & flattening
# --------------------------------------------------------------------------- #

def is_noise(author, body):
    """Return True if a comment should be filtered out of the stream."""
    if author in NOISE_AUTHORS:
        return True
    if body.strip() in NOISE_BODIES:
        return True
    if not body.strip():
        return True
    return False


def walk_comments(children, lines):
    """Recursively walk the nested comment tree, appending clean comment text.

    Reddit nests replies as: comment -> data -> replies -> data -> children.
    The `replies` field is "" (empty string) for leaf comments, so we guard
    against that before recursing. Non-comment nodes (e.g. "more" stubs that
    use kind "more") are skipped.
    """
    for child in children:
        if child.get("kind") != "t1":
            continue

        data = child.get("data", {})
        author = data.get("author", "")
        body = data.get("body", "")

        if not is_noise(author, body):
            lines.append(f"Comment by {author}: {body.strip()}")

        # Recurse into replies if they exist (leaf comments have replies == "").
        replies = data.get("replies")
        if isinstance(replies, dict):
            reply_children = replies.get("data", {}).get("children", [])
            walk_comments(reply_children, lines)


def parse_thread(thread_json):
    """Turn raw Reddit thread JSON into a structured, flattened record.

    The thread JSON is a list: index [0] is the parent post listing, index [1]
    is the comment-tree listing. Returns a dict with post_title, source_url, and
    flattened_content, or None if the structure is unexpected.
    """
    try:
        post_listing = thread_json[0]
        comment_listing = thread_json[1]

        post_data = post_listing["data"]["children"][0]["data"]
        title = post_data.get("title", "").strip()
        selftext = post_data.get("selftext", "").strip()
        permalink = post_data.get("permalink", "")
        source_url = "https://www.reddit.com" + permalink if permalink else ""
    except (IndexError, KeyError, TypeError) as exc:
        print(f"  [structure error] unexpected JSON layout: {exc}")
        return None

    # Build the flattened conversational stream, starting with the post itself.
    lines = [f"Post Title: {title}"]
    if selftext:
        lines.append(f"Post Body: {selftext}")

    comment_children = comment_listing.get("data", {}).get("children", [])
    walk_comments(comment_children, lines)

    # Count comment lines for reporting (everything after the post header/body).
    comment_count = sum(1 for line in lines if line.startswith("Comment by "))

    record = {
        "post_title": title,
        "source_url": source_url,
        "flattened_content": "\n".join(lines),
    }
    return record, comment_count


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #

def load_dump(path):
    """Read and parse a single JSON dump file, returning None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"  [read error] {path}: {exc}")
        return None


def save_record(record, post_id):
    """Write a parsed record to raw_data/<post_id>.json."""
    path = os.path.join(OUTPUT_DIR, f"{post_id}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=False)
    return path


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dump_paths = sorted(glob.glob(os.path.join(INPUT_DIR, "*.json")))
    if not dump_paths:
        print(f"No JSON dumps found in {INPUT_DIR}/. Nothing to do.")
        return

    success_count = 0
    for i, path in enumerate(dump_paths, start=1):
        post_id = os.path.splitext(os.path.basename(path))[0]
        print(f"[{i}/{len(dump_paths)}] Parsing: {post_id}")

        thread_json = load_dump(path)
        if thread_json is None:
            print("  -> skipped (read failed)")
            continue

        parsed = parse_thread(thread_json)
        if parsed is None:
            print("  -> skipped (parse failed)")
            continue

        record, comment_count = parsed
        out_path = save_record(record, post_id)
        char_count = len(record["flattened_content"])
        print(
            f"  -> saved {out_path} "
            f"({char_count} chars, {comment_count} comments kept)"
        )
        success_count += 1

    print(f"\nDone. {success_count}/{len(dump_paths)} threads saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
