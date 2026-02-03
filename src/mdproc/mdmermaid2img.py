# -*- coding: utf-8 -*-
"""
Process Mermaid charts in Markdown documents: Convert → Upload → Replace.

TRUE 3-STEP WORKFLOW (writes file ONCE):
1. convert_mermaid_in_markdown() - Convert mermaid code blocks to images
2. upload_mermaid_images_to_cos() - Upload images to COS
3. replace_mermaid_with_images() - Replace mermaid blocks with image links (local or COS)

Use the unified pipeline: process_mermaid_markdown_3steps()
- Reads file once
- Does all replacements in memory
- Writes file once at the end
"""

from dotenv import load_dotenv

import argparse

import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, List

from .mermaid2img import render_mermaid_cli
from .cos_uploader import upload

load_dotenv()


def extract_mermaid_code(markdown_content: str) -> list[Tuple[str, str]]:
    """
    Extract mermaid code blocks from markdown content.

    Args:
        markdown_content: The markdown text content

    Returns:
        List of tuples (mermaid_code, original_block) where:
        - mermaid_code: Clean mermaid code without markdown fences
        - original_block: Original markdown block including fences
    """
    # Pattern to match ```mermaid ... ```
    pattern = r"```mermaid\n(.*?)\n```"
    matches = re.finditer(pattern, markdown_content, re.DOTALL)

    results = []
    for match in matches:
        mermaid_code = match.group(1).strip()
        original_block = match.group(0)
        results.append((mermaid_code, original_block))

    return results


def mermaid_to_image(
    mermaid_code: str,
    output_dir: Optional[str] = None,
    theme: str = "default",
    scale: int = 2,
) -> str:
    """
    Convert mermaid code to image file.

    Args:
        mermaid_code: Raw mermaid diagram code (without markdown fences)
        output_dir: Directory to save the image. If None, uses temp directory
        theme: Theme for rendering ("default" or "dark")
        scale: Scale factor for image

    Returns:
        Path to the generated image file
    """
    if output_dir is None:
        output_dir = os.path.join(tempfile.gettempdir(), "mermaid2img")

    os.makedirs(output_dir, exist_ok=True)

    # Generate unique filename based on mermaid code hash
    code_hash = hash(mermaid_code) & 0x7FFFFFFF
    output_filename = f"mermaid_{code_hash}.png"
    output_path = os.path.join(output_dir, output_filename)

    # Render mermaid code to image
    render_mermaid_cli(mermaid_code, output_path, theme=theme, scale=scale)

    return output_path


def convert_mermaid_in_markdown(
    markdown_content: str,
    img_output_dir: Optional[str] = None,
    theme: str = "default",
    scale: int = 1,
) -> Tuple[str, Dict[str, str]]:
    """
    Convert all mermaid charts in markdown to images.
    DOES NOT modify markdown content, only generates images.

    Args:
        markdown_content: The markdown text content
        img_output_dir: Directory to save images. If None, uses temp directory
        theme: Theme for rendering ("default" or "dark")
        scale: Scale factor for image

    Returns:
        Tuple of (markdown_unchanged, image_map_dict)
        where image_map_dict contains {original_block: img_path}
    """
    # Extract mermaid blocks
    mermaid_blocks = extract_mermaid_code(markdown_content)

    if not mermaid_blocks:
        print("No mermaid blocks found.")
        return markdown_content, {}

    print(f"Found {len(mermaid_blocks)} mermaid blocks")

    image_map = {}  # {original_block: img_path}

    # Convert each mermaid block to image
    for i, (mermaid_code, original_block) in enumerate(mermaid_blocks, 1):
        try:
            print(f"Converting block {i}/{len(mermaid_blocks)}...")

            # Convert to image
            img_path = mermaid_to_image(mermaid_code, img_output_dir, theme, scale)
            print(f"  Generated: {img_path}")

            # Store mapping
            image_map[original_block] = img_path

        except Exception as e:
            print(f"  Error: {e}")
            continue

    return markdown_content, image_map


def upload_mermaid_images_to_cos(local_image_paths: List[str]) -> Dict[str, str]:
    """
    Upload images to COS and map to URLs.

    Args:
        local_image_paths: List of local image file paths

    Returns:
        Dictionary mapping {img_path: cos_url}
    """
    upload_results = {}

    for i, img_path in enumerate(local_image_paths, 1):
        try:
            print(f"Uploading image {i}/{len(local_image_paths)}...")
            print(f"  Source: {img_path}")

            cos_url = upload(Path(img_path))
            upload_results[img_path] = cos_url
            print(f"  COS URL: {cos_url}")

        except Exception as e:
            print(f"  Upload failed: {e}")
            continue

    return upload_results


def replace_mermaid_with_images(
    markdown_content: str,
    mermaid_to_img_map: Dict[str, str],
    img_to_url_map: Dict[str, str],
) -> str:
    """
    Replace mermaid code blocks with image links (local or COS URLs).

    Args:
        markdown_content: Original markdown text
        mermaid_to_img_map: Dictionary mapping {original_mermaid_block: img_path}
        img_to_url_map: dictionary mapping {img_path: cos_url}. If None, use local paths.
        markdown_path: Path to markdown file (for calculating relative paths)

    Returns:
        Updated markdown content with image links
    """
    updated_content = markdown_content

    for i, (original_block, img_path) in enumerate(mermaid_to_img_map.items(), 1):
        # Determine image URL: COS if available, otherwise local path
        if img_to_url_map and img_path in img_to_url_map:
            image_url = img_to_url_map[img_path]
            print(f"  Using COS URL: {image_url}")
        else:
            raise ValueError(f"No COS URL found for image path: {img_path}")

        # Create markdown image link
        image_link = f"![mermaid {i}]({image_url})"
        # Replace original mermaid block
        updated_content = updated_content.replace(original_block, image_link)

    return updated_content


def process_mermaid_markdown_3steps(
    markdown_path: str,
    output_path: Optional[str] = None,
    theme: str = "default",
    scale: int = 1,
    img_output_dir: Optional[str] = None,
):
    """
    Process markdown in 3 steps: Convert → Upload (optional) → Replace links.
    Write file only ONCE at the end.

    Args:
        markdown_path: Path to input markdown file
        output_path: Path to output markdown file. If None, overwrites input
        upload_to_cos: Whether to upload images to COS
        theme: Theme for rendering ("default" or "dark")
        scale: Scale factor for image
        img_output_dir: Directory to save images. If None, uses temp directory

    Returns:
        Tuple of (final_markdown_content, results_dict)
    """
    # Read markdown file once
    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    if output_path is None:
        output_path = markdown_path

    # ===== STEP 1: Convert mermaid to images =====
    print("STEP 1: Converting mermaid charts to images...")
    _, mermaid_to_img_map = convert_mermaid_in_markdown(
        markdown_content, img_output_dir, theme, scale
    )

    if not mermaid_to_img_map:
        print("No mermaid blocks found. Writing unchanged content.")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return markdown_content, {}

    results = {"images": mermaid_to_img_map}

    # ===== STEP 2: Upload  =====
    print("STEP 2: Uploading images to COS...")
    image_paths = list(mermaid_to_img_map.values())
    img_to_url_map = upload_mermaid_images_to_cos(image_paths)

    if img_to_url_map:
        results["cos_urls"] = img_to_url_map
        print(f"Uploaded {len(img_to_url_map)} images successfully.")

    # ===== STEP 3: Replace in memory =====
    print("STEP 3: Replacing mermaid blocks with image links...")
    final_content = replace_mermaid_with_images(
        markdown_content, mermaid_to_img_map, img_to_url_map
    )

    # Write file ONCE
    print("Writing output file...")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"Output saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert tables in a Markdown file to images and upload to COS."
    )
    parser.add_argument("input_file", help="Path to the input markdown file.")
    args = parser.parse_args()
    input_file = args.input_file

    output_file = f"{os.path.splitext(input_file)[0]}_mm2img.md"
    process_mermaid_markdown_3steps(input_file, output_path=output_file)


if __name__ == "__main__":
    main()
