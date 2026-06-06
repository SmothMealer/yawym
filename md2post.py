#!/usr/bin/env python3
"""Convert a markdown file into a yawym blog post (HTML, index, and feed)."""

from __future__ import annotations

import argparse
import email.utils
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent / "yawym"
BASE_URL = "https://mechanicalcolor.com"
SIGNATURE_EMAIL = "adam@mechanicalcolor.com"

STYLE_BLOCK = """\
<style>
  :root { color-scheme: light dark; }
  p { max-width: 40em; }
</style>"""

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def slugify(title: str) -> str:
    slug = title.lower().strip().rstrip(".")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    return slug


def convert_inline(text: str) -> str:
    return LINK_RE.sub(r'<a href="\2">\1</a>', text)


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_RE.split(text)
    return [part.strip() for part in parts if part.strip()]


def format_paragraph(block: str) -> str:
    lines = block.split("\n")
    content_indent = "  "

    if len(lines) == 1:
        pieces = split_sentences(convert_inline(lines[0]))
        inner = "\n".join(f"{content_indent}{piece}" for piece in pieces)
    else:
        converted = [convert_inline(line.strip()) for line in lines if line.strip()]
        inner_parts: list[str] = []
        for index, piece in enumerate(converted):
            suffix = "<br />" if index < len(converted) - 1 else ""
            inner_parts.append(f"{content_indent}{piece}{suffix}")
        inner = "\n".join(inner_parts)

    return f"<p>\n{inner}\n</p>"


def parse_markdown(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    title: str | None = None
    body_lines: list[str] = []
    index = 0

    while index < len(lines) and not lines[index].strip():
        index += 1

    if index < len(lines) and lines[index].startswith("# "):
        title = lines[index][2:].strip()
        index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1

    body = "\n".join(lines[index:]).strip()
    if not body:
        raise ValueError("markdown file has no body content")

    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", body) if block.strip()]
    if not paragraphs:
        raise ValueError("markdown file has no paragraphs")

    if title is None:
        raise ValueError("markdown file needs a '# Title' heading")

    return title, paragraphs


def build_html(title: str, post_date: date, paragraphs: list[str]) -> str:
    date_str = post_date.isoformat()
    body = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        '<meta charset="utf-8">',
        f"<title>yawym - {title}</title>",
        "",
        STYLE_BLOCK,
        "",
        "<p>",
        '  <a href="index.html">&#171; all posts</a>',
        "</p>",
        "",
        "<p>",
        f"  {date_str}",
        "</p>",
        "",
    ]

    for paragraph in paragraphs:
        body.append(format_paragraph(paragraph))
        body.append("")

    body.extend(
        [
            "<p>",
            "  Adam<br />",
            f'  <a href="mailto:{SIGNATURE_EMAIL}">{SIGNATURE_EMAIL}</a>',
            "</p>",
            "",
        ]
    )

    return "\n".join(body)


def feed_description(paragraphs: list[str]) -> str:
    plain = LINK_RE.sub(r"\1", paragraphs[0])
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= 120:
        return plain
    truncated = plain[:120].rsplit(" ", 1)[0]
    return truncated + "..."


def update_index(html_filename: str, display_title: str, post_date: date) -> None:
    index_path = SITE_DIR / "index.html"
    content = index_path.read_text(encoding="utf-8")
    date_str = post_date.isoformat()
    new_line = (
        f'  <a href="{html_filename}">{display_title}</a> {date_str}<br />\n'
    )

    posts_match = re.search(
        r"(<p>\n)(  <a href=\"20\d{2}-\d{2}-\d{2}-)",
        content,
    )
    if not posts_match:
        raise ValueError("could not find posts list in index.html")

    insert_at = posts_match.start(2)
    updated = content[:insert_at] + new_line + content[insert_at:]
    index_path.write_text(updated, encoding="utf-8")


def update_feed(
    html_filename: str,
    display_title: str,
    post_date: date,
    paragraphs: list[str],
) -> None:
    feed_path = SITE_DIR / "feed.xml"
    content = feed_path.read_text(encoding="utf-8")
    post_url = f"{BASE_URL}/{html_filename}"
    pub_dt = datetime(
        post_date.year,
        post_date.month,
        post_date.day,
        tzinfo=timezone.utc,
    )
    pub_date = email.utils.format_datetime(pub_dt, usegmt=True)
    description = feed_description(paragraphs)

    item = f"""    <item>
      <title>{display_title}</title>
      <link>{post_url}</link>
      <guid>{post_url}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[{description}]]></description>
    </item>
"""

    channel_end = content.find("    <item>")
    if channel_end == -1:
        raise ValueError("could not find items in feed.xml")

    updated = content[:channel_end] + item + content[channel_end:]
    feed_path.write_text(updated, encoding="utf-8")


def convert_markdown(
    markdown_path: Path,
    post_date: date | None = None,
    dry_run: bool = False,
) -> Path:
    post_date = post_date or date.today()
    title, paragraphs = parse_markdown(markdown_path.read_text(encoding="utf-8"))
    display_title = title.rstrip(".")
    html_filename = f"{post_date.isoformat()}-{slugify(title)}.html"
    html_path = SITE_DIR / html_filename
    html_content = build_html(title, post_date, paragraphs)

    if html_path.exists() and not dry_run:
        raise ValueError(f"refusing to overwrite existing file: {html_path}")

    if dry_run:
        print(f"Would write: {html_path}")
        print(f"Would update: {SITE_DIR / 'index.html'}")
        print(f"Would update: {SITE_DIR / 'feed.xml'}")
        print()
        print(html_content)
        return html_path

    html_path.write_text(html_content, encoding="utf-8")
    update_index(html_filename, display_title, post_date)
    update_feed(html_filename, display_title, post_date, paragraphs)

    print(f"Wrote {html_path}")
    print(f"Updated {SITE_DIR / 'index.html'}")
    print(f"Updated {SITE_DIR / 'feed.xml'}")
    return html_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a markdown file into a yawym blog post.",
    )
    parser.add_argument("markdown", type=Path, help="path to the markdown file")
    parser.add_argument(
        "--date",
        type=lambda value: date.fromisoformat(value),
        help="post date (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print output without writing files",
    )
    args = parser.parse_args()

    if not args.markdown.is_file():
        print(f"error: file not found: {args.markdown}", file=sys.stderr)
        return 1

    try:
        convert_markdown(args.markdown, post_date=args.date, dry_run=args.dry_run)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
