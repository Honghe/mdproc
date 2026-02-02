"""
Markdown table to image and Uploader to COS.
table with few columns: the table unfolds naturally.
table with many columns: the table is spread out horizontally.
"""

import argparse
import os
import re
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from markdown_it import MarkdownIt
from playwright.sync_api import sync_playwright

from .cos_uploader import upload

load_dotenv()


def extract_tables(md_text):
    # re is simple than markdown-it table extractor for our use case
    table_pattern = re.compile(r"(?:^\s*\|.*\|\s*\n)+", re.MULTILINE)
    return [m.group(0) for m in table_pattern.finditer(md_text)]


def table_to_image(md_text, output_path):
    # md_text = """
    # | A | B | C | D | E | F | G |
    # |---|---|---|---|---|---|---|
    # | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
    # """

    html_table = (
        MarkdownIt("gfm-like", {"linkify": False}).enable("table").render(md_text)
    )
    html_table = html_table.replace("<table", '<table id="mdtable2img"', 1)

    html = f"""
    <html>
    <head>
    <style>
    table {{
    border-collapse: collapse;
    width: max-content;
    table-layout: fixed;
    font-size: 14px;
    }}
    td, th {{
    border: 1px solid #333;
    padding: 6px 10px;
    word-break: break-word;
    }}
    </style>
    </head>
    <body>
    {html_table}
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 2000, "height": 800})
        page.set_content(html)
        table_locator = page.locator("#mdtable2img")
        table_locator.screenshot(path=output_path)
        browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Convert tables in a Markdown file to images and upload to COS."
    )
    parser.add_argument("input_file", help="Path to the input markdown file.")
    args = parser.parse_args()
    input_file = args.input_file

    output_file = f"{os.path.splitext(input_file)[0]}_table2img.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Directory to store temporary imgs
    img_dir = os.path.join(tempfile.gettempdir(), "mdtable2img")
    os.makedirs(img_dir, exist_ok=True)

    # Process tables and convert to images
    tables = extract_tables(content)
    print(f"Find {len(tables)} tables")
    images = []
    for i, table_md in enumerate(tables):
        img_path = os.path.join(img_dir, f"table_{i + 1}.png")
        table_to_image(table_md, img_path)
        print(f"Converted table {i + 1} to image: {img_path}")
        images.append(img_path)
    print(f"Converted {len(images)} tables to images.")

    # Upload images to COS and replace in markdown
    for i, img_path in enumerate(images):
        cos_url = upload(Path(img_path))
        # Replace the first occurrence of the table markdown with image markdown
        table_md = tables[i]
        img_md = f"![Table {i + 1}]({cos_url})\n"
        content = content.replace(table_md, img_md, 1)
    print(f"Uploaded {len(images)} table images to COS.")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Processed markdown saved to {output_file}")


if __name__ == "__main__":
    main()
