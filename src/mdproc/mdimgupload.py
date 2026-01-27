"""
Markdown Image Uploader to COS
"""
import httpx

import argparse

from pathlib import Path

import hashlib
import os
import re
import tempfile

from dotenv import load_dotenv
from .cos_uploader import upload

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Upload images in a Markdown file to COS."
    )
    parser.add_argument("input_file", help="Path to the input markdown file.")
    args = parser.parse_args()
    input_file = args.input_file

    output_file = f"{os.path.splitext(input_file)[0]}_output.md"

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Directory to store temporary imgs
    img_dir = os.path.join(tempfile.gettempdir(), "mdimgupload")
    os.makedirs(img_dir, exist_ok=True)

    # Regex to match img URLs in markdown image tags
    pattern = re.compile(r"!\[(.*?)\]\((https?://[^\s)]+?\.(?:png|jpg|jpeg))\)")
    # Find all img links match group 2
    matches = list(pattern.finditer(content))
    print(f"Find {len(matches)} img links")

    # download imgs
    url_paths = {}  # Map from img URL to local img path
    for match in matches:
        url = match.group(2)
        if url in url_paths:
            img_path = url_paths[url]
            print(f"Reusing img for {url} -> {img_path}")
            continue
        # Use a hash or basename for unique filename
        basename = os.path.basename(url)
        name, ext = os.path.splitext(basename)
        # Use hash to avoid collision
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        img_filename = f"{name}_{url_hash}{ext}"
        img_path = os.path.join(img_dir, img_filename)

        # Download the img to local path
        print(f"Downloading {url}")
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()

        with open(img_path, "wb") as f:
            f.write(resp.content)
        print(f"Saved img to {img_path}")

        url_paths[url] = img_path

    # upload imgs to COS
    img_to_url_map = {}
    for url, img_path in url_paths.items():
        print(f"Uploading {img_path}")
        img_url = upload(Path(img_path))
        img_to_url_map[url] = img_url
        print(f"Uploaded to COS: {img_url}")

    # Replace all occurrences of the img URLs in the content img tags
    def replace_img_with_url(match):
        img_url = match.group(2)
        return f"![{match.group(1)}]({img_to_url_map.get(img_url)})"

    new_content = pattern.sub(replace_img_with_url, content)

    # Write the modified content to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Written output to {output_file}")


if __name__ == "__main__":
    main()
