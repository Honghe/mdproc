# -*- coding: utf-8 -*-
"""
Render Mermaid diagrams to images using Playwright.
Alternative to mermaid-cli that uses browser rendering.
"""

import os
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright


def render_mermaid_playwright(
    mermaid_code: str,
    output_path: str,
    theme: str = "default",
    background_color: str = "white",
    scale: float = 2.0,
    layout: str = "elk",
) -> None:
    """
    Render mermaid diagram to PNG image using Playwright.

    Args:
        mermaid_code: Raw mermaid diagram code (without ```mermaid fences)
        output_path: Path to save the output PNG image
        theme: Mermaid theme ("default", "dark", "forest", "neutral")
        background_color: Background color (CSS color)
        scale: Device scale factor for higher resolution (default 2.0)
        layout: Layout engine for flowchart ("dagre" or "elk"). Only applies to flowchart type.

    Raises:
        RuntimeError: If rendering fails
    """
    # Determine if we need flowchart layout config
    # ELK layout only works for flowchart diagrams
    is_flowchart = "flowchart" in mermaid_code.lower()

    if is_flowchart and layout != "dagre":
        flowchart_config = f"""
            flowchart: {{
                defaultRenderer: '{layout}'
            }},"""
    else:
        flowchart_config = ""

    # Get the absolute path to your local bundle
    assets_dir = Path(__file__).parent / "assets"
    # Copy from https://github.com/Honghe/mermaid-bundle/blob/master/mermaid.bundle.js
    mermaid_bundle_path = (assets_dir / "mermaid.bundle.js").absolute().as_uri()

    # HTML template with Mermaid.js
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="{mermaid_bundle_path}"></script>
    <script type="module">
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: '{theme}',
            securityLevel: 'loose',
            {flowchart_config}
        }});
    </script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background-color: {background_color};
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        #diagram {{
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <div class="mermaid" id="diagram">
{mermaid_code}
    </div>
</body>
</html>
"""

    html_content = html_template.format(
        theme=theme,
        background_color=background_color,
        mermaid_code=mermaid_code,
        flowchart_config=flowchart_config,
        mermaid_bundle_path=mermaid_bundle_path,
    )

    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False
    ) as f:
        temp_html_path = f.name
        f.write(html_content)

    try:
        with sync_playwright() as p:
            # Launch browser in headless mode
            browser = p.chromium.launch(
                headless=True,
            )
            context = browser.new_context(
                viewport={"width": 800, "height": 800},
                device_scale_factor=scale,
            )
            page = context.new_page()

            # Load HTML file
            page.goto(f"file://{Path(temp_html_path).as_posix()}")

            # Wait for mermaid to render
            page.wait_for_selector("#diagram svg", timeout=3000)

            # Get the SVG element for precise cropping
            diagram = page.locator("#diagram")

            # Take screenshot
            diagram.screenshot(path=output_path, type="png")

            browser.close()

    except Exception as e:
        raise RuntimeError(f"Failed to render mermaid diagram: {e}")

    finally:
        # Clean up temporary HTML file
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)


def main():
    """Demo: render mermaid diagram using Playwright."""

    demo_code = """
flowchart TD
    A[开始] --> B["Popen()"]
    B --> C[子进程启动<br>独立运行]
    B --> D[主进程继续执行]
    D --> E{需要<br>子进程结果?}
    E -->|否| D
    E -->|是| F["P.wait()"]
    F -->|阻塞等待| G[子进程结束]
    G --> H[拿到 returncode]
    H --> I[可安全读 stdout/stderr<br>（如果用了 PIPE）]
    I --> J[结束]
"""

    # Create output directory
    img_dir = os.path.join(tempfile.gettempdir(), "mermaid2img")
    os.makedirs(img_dir, exist_ok=True)
    output_path = os.path.join(img_dir, "output_playwright.png")

    print("Rendering mermaid diagram with Playwright...")
    render_mermaid_playwright(
        demo_code,
        output_path,
        theme="default",
        background_color="white",
        scale=2.0,
        layout="elk",
    )
    print(f"Image saved to: {output_path}")


if __name__ == "__main__":
    main()
