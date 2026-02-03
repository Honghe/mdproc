# mdproc

A simple Python tool to process markdown files.

## Features

- Markdown Image Uploader to COS.
- Convert Markdown tables to images and upload to COS.
- Convert mermaid chart to image. (dependency `npm install -g @mermaid-js/mermaid-cli`)

## Config

`.env` or configure environment variables:

```
COS_SECRET_ID=<xyz>
COS_SECRET_KEY=<xyz>
COS_REGION=<xyz>
COS_BUCKET=<xyz>
```

## Usage

- Install dependencies:
  ```bash
  pip install mdproc
  # for md-table2img
  playwright install chromium
  ```
- Markdown images upload:
  ```bash
  mdproc-imgupload your_markdown.md
  ```
- Markdown table to image:
  ```bash
   mdproc-table2img your_markdown.md
  ```
- Markdown mermaid to image:
  ```bash
   mdproc-mermaid2img your_markdown.md
  ```

## Demo

demo.md:

```
![first-version](https://www.python.org/static/img/python-logo.png)
```

demo_output.md

```
![first-version](https://pic-1251484506.cos.ap-guangzhou.myqcloud.com/imgs/python-logo_ae79195a.png)
```

## mermaid2img Benchmark

Note: Browser is Chromium. mermaid-cli use puppeteer.

| mermaid2img | Cold Start /s | Warm Start /s |
| --------------------------------- | ------------- | ------------- |
| playwright (memaidjs cdn) | 2.5 | 1.5 |
| playwright (local mermaid bundle) | 2.5 | 1.5 |
| mermaid-cli | 5.7 | 3.7 |

## License

Apache License
