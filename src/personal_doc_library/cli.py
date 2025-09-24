"""Command-line utilities for the Personal Document Library."""

from __future__ import annotations

import argparse
from typing import Sequence

from personal_doc_library.core.config import config
from personal_doc_library.utils import check_indexing_status, show_config
from personal_doc_library.utils.find_unindexed import find_unindexed_documents
from personal_doc_library.utils.fix_skipped_file import update_book_index_entry
from personal_doc_library.indexing import manage_failed_pdfs


def handle_config_command() -> int:
    """Display current configuration information."""
    show_config.main()
    return 0


def handle_ensure_dirs_command() -> int:
    """Ensure all configured directories exist."""
    config.ensure_directories()
    info = config.get_config_info()
    print("✅ Ensured directories exist:")
    print(f"  Books: {info['books_directory']}")
    print(f"  Database: {info['db_directory']}")
    print(f"  Logs: {info['logs_directory']}")
    return 0


def handle_index_status_command() -> int:
    """Report indexing status."""
    check_indexing_status.main()
    return 0


def handle_find_unindexed_command() -> int:
    """List documents that have not been indexed yet."""
    config.ensure_directories()
    unindexed = find_unindexed_documents()
    total = len(unindexed)
    if total == 0:
        print("✅ All tracked documents are indexed")
        return 0

    print(f"❌ {total} document(s) pending indexing:")
    for path in unindexed:
        print(f"  - {path}")
    return 0


def handle_fix_skipped_command(relative_path: str) -> int:
    """Update the stored hash for a skipped file so it is not reprocessed."""
    try:
        update_book_index_entry(relative_path)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ {exc}")
        return 1
    print(f"✅ Updated hash for {relative_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the pdlib-cli command."""
    parser = argparse.ArgumentParser(prog="pdlib-cli", description="Utilities for the Personal Document Library")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("config", help="Show configuration information")
    subparsers.add_parser("ensure-dirs", help="Create configured directories if they are missing")
    subparsers.add_parser("index-status", help="Show indexing health information")
    subparsers.add_parser("find-unindexed", help="List documents that have not been indexed")

    fix_parser = subparsers.add_parser("fix-skipped", help="Update hash information for a skipped file")
    fix_parser.add_argument("relative_path", help="Document path relative to the books directory")

    manage_parser = subparsers.add_parser("manage-failed", help="Delegate to manage-failed command group")
    manage_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to manage_failed_pdfs")

    args = parser.parse_args(argv)

    if args.command == "config":
        return handle_config_command()
    if args.command == "ensure-dirs":
        return handle_ensure_dirs_command()
    if args.command == "index-status":
        return handle_index_status_command()
    if args.command == "find-unindexed":
        return handle_find_unindexed_command()
    if args.command == "fix-skipped":
        return handle_fix_skipped_command(args.relative_path)
    if args.command == "manage-failed":
        extra_args = args.args or None
        return manage_failed_pdfs.main(extra_args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
