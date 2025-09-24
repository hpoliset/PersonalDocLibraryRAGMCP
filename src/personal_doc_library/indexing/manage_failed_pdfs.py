"""Utilities for inspecting and repairing failed indexing attempts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Iterable

from personal_doc_library.core.shared_rag import SharedRAG
from personal_doc_library.core.config import config


def show_failed_pdfs() -> None:
    """Display a summary of failed PDF processing attempts."""
    rag = SharedRAG()
    report = rag.get_failed_pdfs_report()

    print("=== Failed PDFs Report ===")
    print(f"Total failed: {report['total_failed']}")

    if report["total_failed"] == 0:
        print("✅ No failed PDFs!")
        return

    print("\n📊 By Error Type:")
    for error_type, pdfs in report["by_error_type"].items():
        print(f"  {error_type}: {len(pdfs)} files")
        for pdf in list(pdfs)[:5]:
            print(f"    - {pdf}")
        if len(pdfs) > 5:
            print(f"    ... and {len(pdfs) - 5} more")

    print("\n📋 Detailed Failed PDFs:")
    for pdf_name, info in report["failed_pdfs"].items():
        print(f"\n📄 {pdf_name}")
        print(f"   Error: {info.get('error', 'Unknown')}")
        print(f"   Failed at: {info.get('failed_at', 'Unknown')}")
        print(f"   Retry count: {info.get('retry_count', 0)}")
        print(f"   Size: {info.get('file_size', 0):,} bytes")
        print(f"   Path: {info.get('relative_path', 'Unknown')}")


def clear_failed_pdf(pdf_name: str) -> None:
    """Clear a specific PDF from the failed list."""
    rag = SharedRAG()
    if rag.clear_failed_pdf(pdf_name):
        print(f"✅ Cleared {pdf_name} from failed list")
    else:
        print(f"❌ Could not clear {pdf_name}")


def retry_failed_pdfs(*, max_retries: int = 3, timeout_minutes: int = 10) -> Iterable[str]:
    """Retry processing failed PDFs and yield successful entries."""
    rag = SharedRAG()
    print(
        "🔄 Retrying failed PDFs "
        f"(max retries: {max_retries}, timeout: {timeout_minutes}min)"
    )

    retried = rag.retry_failed_pdfs(
        max_retries=max_retries,
        timeout_minutes=timeout_minutes,
    )

    if retried:
        print(f"✅ Successfully processed {len(retried)} PDFs:")
        for pdf in retried:
            print(f"  - {pdf}")
        return retried

    print("❌ No PDFs were successfully processed")
    return []


def clear_all_failed() -> None:
    """Clear all failed PDFs from the on-disk tracking file."""
    failed_pdfs_file = config.db_directory / "failed_pdfs.json"

    if failed_pdfs_file.exists():
        failed_pdfs_file.unlink()
        print("✅ Cleared all failed PDFs from the list")
    else:
        print("ℹ️  No failed PDFs file found")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Manage failed indexing attempts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show", help="Display a report of failed PDFs")

    clear_parser = subparsers.add_parser("clear", help="Remove a specific PDF from the failed list")
    clear_parser.add_argument("pdf_name", help="Relative path of the PDF to clear")

    retry_parser = subparsers.add_parser("retry", help="Retry processing failed PDFs")
    retry_parser.add_argument("--timeout", type=int, default=10, help="Timeout per document in minutes")
    retry_parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries per document")

    subparsers.add_parser("clear-all", help="Clear all failed entries")

    args = parser.parse_args(argv)

    if args.command == "show":
        show_failed_pdfs()
        return 0
    if args.command == "clear":
        clear_failed_pdf(args.pdf_name)
        return 0
    if args.command == "retry":
        retry_failed_pdfs(max_retries=args.max_retries, timeout_minutes=args.timeout)
        return 0
    if args.command == "clear-all":
        clear_all_failed()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
