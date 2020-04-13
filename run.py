import logging
import sys
import textwrap
import json
import hashlib
from slugify import slugify
import os
import pprint
from pyzotero import zotero

logger = logging.getLogger(__name__)

IMPORTED_TAG = "notable-imported"


HEADER_TEMPLATE = """---
title: "{title}"
created: '{timestamp}'
modified: '{timestamp}'
tags: [{tags}]
attachments: [{attachments}]
---\n"""


def make_slug(item):
    title = slugify(item["shortTitle"] or item["title"])[:60]
    url = item["url"]
    hasher = hashlib.md5()
    hasher.update(url.encode())
    h = hasher.hexdigest()[:8]
    return f"paper-{title}-{h}"


def main():
    library_id = os.environ["ZOTERO_LIBRARY_ID"]
    api_key = os.environ["ZOTERO_API_KEY"]
    library_type = "user"
    logger.info(f"Running for library {library_id}")

    with open(os.path.expanduser("~/.notable.json")) as f:
        notable_dir = json.load(f)["cwd"]
        logger.info(f"notable directory found at {notable_dir}")

    notes_dir = os.path.join(notable_dir, "notes")
    attach_dir = os.path.join(notable_dir, "attachments")

    zot = zotero.Zotero(library_id, library_type, api_key)
    items = zot.top(tag=f"-{IMPORTED_TAG}")
    logger.info(f"Found {len(items)} to process")

    for item in items:
        title = item["data"]["title"]
        logger.info(f"Processing '{title}'")

        children = zot.children(item["data"]["key"], itemType="attachment")
        pdfs = [c for c in children if c["data"]["contentType"] == "application/pdf"]

        if len(pdfs) != 1:
            logger.warning(
                f"--> Item didn't have only 1 attachment (had {len(pdfs)}), skipping"
            )
            continue

        item_slug = make_slug(item["data"])
        pdf_filename = item_slug + ".pdf"

        # Download the PDF
        pdf = pdfs[0]
        pdf_path = os.path.join(attach_dir, pdf_filename)
        logger.info(f"--> Downloading PDF to {pdf_path}")
        if os.path.exists(pdf_path):
            logger.warning(f"File already exists at pdf path, skipping item")
            continue

        zot.dump(pdf["data"]["key"], pdf_path)

        # Build the markdown
        logger.info("--> Building markdown")
        tags = ["progress/untagged", "papers"]

        for tag in item["data"]["tags"]:
            tag = tag["tag"]
            if tag in {"_tablet"}:
                continue
            tags.append(f"papers/source/{tag}")

        note_header = HEADER_TEMPLATE.format(
            title=title,
            timestamp=item["data"]["dateAdded"],
            tags=",".join(tags),
            attachments=pdf_filename,
        )
        note_body_lines = []
        note_body_lines.append("### Notes")
        note_body_lines.append("")
        note_body_lines.append("### Metadata")
        note_body_lines.append(f"**Title**: {title}")

        authors = ", ".join(x["lastName"] or x["name"] for x in item["data"]["creators"])
        note_body_lines.append(f"**Authors**: {authors}")

        date = item["data"]["date"]
        note_body_lines.append(f"**Date**: {date}")

        abstract = item["data"]["abstractNote"]
        note_body_lines.append(f"**Abstract**: {abstract}")

        accessed = item["data"]["accessDate"]
        note_body_lines.append(f"**Accessed**: {accessed}")

        url = item["data"]["url"]
        note_body_lines.append(f"**Original URL**: {url}")

        note_body_lines.append(f"**PDF**: [](@attachment/{pdf_filename})")

        note_text = note_header + "\n" + "\n".join(note_body_lines)

        note_path = os.path.join(notes_dir, item_slug + ".md")
        logger.info(f"--> Writing note to {note_path}")
        if os.path.exists(note_path):
            logger.warning("--> Note already exists at path, skipping")
            continue

        with open(note_path, "w") as f:
            f.write(note_text)

        logger.info(f"--> Adding '{IMPORTED_TAG}' tag")
        zot.add_tags(item, IMPORTED_TAG)

        logger.info(f"--> Deleting PDF attachment in zotero")
        zot.delete_item(pdfs[0])

        # TODO: zotero item seems to have a version. If that changes, could re-update at least the metadata? cautious about overwriting file though
    logger.info("All done")


if __name__ == "__main__":
    LOGGING_FORMAT = "%(levelname)s:\t%(asctime)-15s %(message)s"
    logging.basicConfig(stream=sys.stdout, format=LOGGING_FORMAT, level=logging.INFO)
    main()
