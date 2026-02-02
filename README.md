# mdproc

A simple Python tool to process markdown files.

## Features

- Markdown Image Uploader to COS.
- Convert Markdown tables to images and upload to COS.

## Config

`.env` or configure environment variables:
```
COS_SECRET_ID=<xyz>
COS_SECRET_KEY=<xyz>
COS_REGION=<xyz>
COS_BUCKET=<xyz>
```

## Usage

1. Install dependencies:
    ```bash
    pip install mdproc
    playwright install chromium
    ```
2. Run the script:
    ```bash
    mdproc-imgupload your_markdown.md
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

## License

Apache License