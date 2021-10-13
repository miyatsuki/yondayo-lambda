from itertools import cycle
from typing import List
import boto3
import requests
from PIL import Image


def create_image(image_url: List[str], user_name: str, title: str):
    size = (1200, 630)
    base = Image.new("RGB", size, (256, 256, 256))
    left_top = (0, 0)

    images = []
    for i, url in enumerate(image_url):
        r = requests.get(url)
        suffix = url.split(".")[-1]
        file_name = f"/tmp/{i}.{suffix}"
        with open(f"/tmp/{i}.{suffix}", "wb") as f:
            f.write(r.content)

        images.append(file_name)

    for image_name in cycle(images):
        image = Image.open(image_name)
        width, height = image.size

        w_scale = (size[0] - left_top[0]) / width
        w_scale_height = height * w_scale

        h_scale = (size[1] - left_top[1]) / height
        h_scale_width = width * h_scale

        if w_scale_height + left_top[1] <= size[1]:
            scale = w_scale
            fit = "width"
        else:
            scale = h_scale
            fit = "height"

        if width * scale <= 1 or height * scale <= 1:
            break

        resized_size = (int(width * scale), int(height * scale))
        image_resized = image.resize(resized_size)
        base.paste(image_resized, left_top)

        if fit == "height":
            left_top = (left_top[0] + resized_size[0], left_top[1])
        else:
            left_top = (left_top[0], left_top[1] + resized_size[1])

        if left_top[0] >= size[0] or left_top[1] >= size[1]:
            break

    base.save("/tmp/out.png")

    s3 = boto3.client("s3")  # S3オブジェクトを取得
    s3.upload_file(
        "/tmp/out.png",
        "yondayo",
        f"ogp/{user_name}/{title}.png",
        ExtraArgs={"ACL": "public-read"},
    )

    url = f"https://yondayo.s3.ap-northeast-1.amazonaws.com/ogp/{user_name}/{title}.png"

    print("end")

    return {"statusCode": 200, "body": url}
