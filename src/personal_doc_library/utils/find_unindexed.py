"""Utility helpers for discovering unindexed PDFs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from personal_doc_library.core.config import config

SUPPORTED_EXTENSIONS = (".pdf",)


def collect_pdfs(books_directory: Path) -> list[str]:
    """Return all supported documents relative to the books directory."""
    documents: list[str] = []
    for path in books_directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(str(path.relative_to(books_directory)))
    return documents


def load_indexed_paths(index_file: Path) -> Iterable[str]:
    """Load indexed document paths if the index exists."""
    if not index_file.exists():
        return []
    with index_file.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.keys()


def find_unindexed_documents(books_directory: Path | None = None, index_file: Path | None = None) -> list[str]:
    """Return a sorted list of unindexed document paths."""
    books_dir = books_directory or config.books_directory
    index_path = index_file or (config.db_directory / "book_index.json")
    all_documents = set(collect_pdfs(books_dir))
    indexed_documents = set(load_indexed_paths(index_path))
    return sorted(all_documents - indexed_documents)


def main() -> None:
    """Command line helper for displaying unindexed documents."""
    config.ensure_directories()
    books_dir = config.books_directory
    index_path = config.db_directory / "book_index.json"

    unindexed = find_unindexed_documents(books_dir, index_path)
    total = len(list(collect_pdfs(books_dir)))
    indexed = total - len(unindexed)

    print(f"Total PDFs: {total}")
    print(f"Indexed PDFs: {indexed}")
    print(f"Unindexed PDFs: {len(unindexed)}")
    print("\nUnindexed PDFs:")
    for pdf in unindexed:
        print(f"  - {pdf}")


if __name__ == "__main__":
    main()
