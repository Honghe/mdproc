import tempfile
import os
import shutil
import subprocess


def render_mermaid_cli(code: str, output_path: str, theme="default", scale=1):
    """
    Render mermaid code to image using mermaid-cli.
    Supports Chinese and other Unicode characters.
    """
    mmdc_path = os.environ.get("MMDC_PATH") or shutil.which("mmdc")
    if mmdc_path and os.name == "nt":
        candidate_cmd = f"{mmdc_path}.cmd"
        if os.path.exists(candidate_cmd):
            mmdc_path = candidate_cmd
    if not mmdc_path:
        raise FileNotFoundError(
            "mmdc not found. Add it to PATH or set MMDC_PATH to the full path "
        )

    cmd = [
        mmdc_path,
        "-i",
        "-",
        "-o",
        output_path,
        "--theme",
        theme,
        "--scale",
        str(scale),
        "--backgroundColor",
        "white",
    ]

    process = subprocess.run(
        cmd,
        input=code.encode(
            "utf-8"
        ),  # Explicitly specify UTF-8 encoding to support Chinese
        capture_output=True,
        text=False,  # Receive as bytes to avoid encoding issues
    )

    if process.returncode != 0:
        stderr_msg = process.stderr.decode("utf-8", errors="replace")
        print("Error:", stderr_msg)
        raise RuntimeError(f"mermaid-cli execution failed: {stderr_msg}")


def main():
    demo_code = """
    flowchart TD
        A[开始] --> B{Is it?}
        B -->|Yes| C[OK]
        C --> D[Rethink]
        D --> B
        B ---->|No| E[End]
    """

    img_dir = os.path.join(tempfile.gettempdir(), "mermaid2img")
    os.makedirs(img_dir, exist_ok=True)
    output_path = os.path.join(img_dir, "output.png")
    render_mermaid_cli(demo_code, output_path, theme="default", scale=1)
    print(f"Image saved to: {output_path}")


if __name__ == "__main__":
    main()
