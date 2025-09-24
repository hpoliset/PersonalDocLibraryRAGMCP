"""Utilities for repairing skipped document entries in the book index."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from personal_doc_library.core.config import config


def calculate_md5(filepath: Path) -> str:
    """Calculate the MD5 hash for a file."""
    hash_md5 = hashlib.md5()
    with filepath.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def update_book_index_entry(relative_path: str) -> bool:
    """Update the stored hash for the given relative document path."""
    index_path = config.db_directory / "book_index.json"
    if not index_path.exists():
        raise FileNotFoundError("book_index.json does not exist; run indexing first.")

    with index_path.open("r", encoding="utf-8") as handle:
        book_index = json.load(handle)

    if relative_path not in book_index:
        raise KeyError(f"{relative_path} not found in book index")

    target_file = config.books_directory / relative_path
    if not target_file.exists():
        raise FileNotFoundError(f"{target_file} does not exist")

    actual_hash = calculate_md5(target_file)
    entry = book_index[relative_path]
    entry["hash"] = actual_hash
    entry.setdefault("note", "Manually marked as processed")

    with index_path.open("w", encoding="utf-8") as handle:
        json.dump(book_index, handle, indent=2)

    return True


def main() -> None:
    """CLI helper for updating a single book index entry."""
    import argparse

    parser = argparse.ArgumentParser(description="Update the stored hash for a skipped file.")
    parser.add_argument("relative_path", help="Path to the document relative to the books directory")
    args = parser.parse_args()

    try:
        update_book_index_entry(args.relative_path)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ {exc}")
    else:
        print(f"✅ Updated hash for {args.relative_path}")


if __name__ == "__main__":
    main()
