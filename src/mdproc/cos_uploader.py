# -*- coding=utf-8
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from qcloud_cos import CosConfig, CosS3Client

load_dotenv()

secret_id = os.environ["COS_SECRET_ID"]
secret_key = os.environ["COS_SECRET_KEY"]
COS_REGION = os.environ["COS_REGION"]
COS_BUCKET = os.environ["COS_BUCKET"]
COS_URL_PREFIX = f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/"

token = None  # To use the temporary key, a Token is required. By default, it is empty.
scheme = "https"
config = CosConfig(
    Region=COS_REGION,
    SecretId=secret_id,
    SecretKey=secret_key,
    Token=token,
    Scheme=scheme,
)
cos_client = CosS3Client(config)


def upload(png_path: Path) -> str:
    png_filename = png_path.name
    cos_key = f"imgs/{png_filename}"
    with open(png_path, "rb") as fp:
        cos_client.put_object(
            Bucket=COS_BUCKET,
            Body=fp,
            Key=cos_key,
            StorageClass="STANDARD",
            ContentType="image/png",
        )
    png_url = COS_URL_PREFIX + cos_key
    return png_url

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # Use the directory of this script for demo.png
    dir = Path(__file__).parent.resolve()
    png_path = dir / "demo.png"
    png_url = upload(png_path)
    print(f"Uploaded to COS: {png_url}")
