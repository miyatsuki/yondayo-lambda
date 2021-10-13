import json
import pathlib
from typing import List
import boto3
import requests
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("KleeOne-Regular.ttf", 40)
small_font = ImageFont.truetype("KleeOne-Regular.ttf", 20)

row_height = 180


def create_row(
    title: str,
    image_file: pathlib.Path,
    before_proceed: int,
    after_proceed: int,
    total: int,
):
    row = Image.new("RGB", (1200, row_height), (256, 256, 256))

    image = Image.open(image_file)
    width, height = image.size

    scale_h = row_height / height
    scale_w = 200 / width
    scale = min(scale_h, scale_w)

    resized_size = (int(width * scale), int(height * scale))
    image_resized = image.resize(resized_size)
    width, height = image_resized.size

    row.paste(image_resized, (int((200 - width) / 2), int((row_height - height) / 2)))
    draw = ImageDraw.Draw(row)

    title_width = 600
    truncated_title = title
    while font.getsize(truncated_title)[0] > title_width:
        truncated_title = truncated_title[:-1]

    if truncated_title != title:
        title = truncated_title + "..."

    draw.text((200, 30), title, (0, 0, 0), font=font, anchor="lt")
    draw.text(
        (1150, 30),
        f"{after_proceed}/{total} (+{after_proceed - before_proceed})",
        (0, 0, 0),
        font=font,
        anchor="rt",
    )

    width = 1150 - 200
    # 全体
    draw.rectangle(
        (200, 30 + 60, 1150, row_height - 30), fill=(0, 0, 0), outline=(0, 0, 0)
    )
    # 今回進捗
    draw.rectangle(
        (200, 30 + 60, 200 + int(width * after_proceed / total), row_height - 30),
        fill=(255, 0, 0),
        outline=(255, 0, 0),
    )
    # 前回進捗
    draw.rectangle(
        (200, 30 + 60, 200 + int(width * before_proceed / total), row_height - 30),
        fill=(0, 255, 0),
        outline=(0, 255, 0),
    )

    # completeの場合は追加処理
    if after_proceed == total:
        draw.rectangle(
            (200, 30 + 60, 1150, row_height - 30),
            fill=(0, 255, 0),
            outline=(0, 255, 0),
        )
        draw.text(
            (int((200 + 1150) / 2), int((90 + row_height - 30) / 2)),
            "COMPLETE!",
            (0, 0, 0),
            font=font,
            anchor="mm",
        )

    return row


def handler(event, context):
    print(event)
    payload = event["body"]
    data = json.loads(payload)

    proceeds = data["proceeds"]
    user_name = data["user_name"]
    date_range = data["date_range"]

    size = (1200, 630)
    base = Image.new("RGB", size, (256, 256, 256))

    for i, proceed in enumerate(proceeds):
        image_url = proceed["image_url"]
        r = requests.get(image_url)
        suffix = image_url.split(".")[-1]
        file_name = f"/tmp/{i}.{suffix}"
        with open(file_name, "wb") as f:
            f.write(r.content)
        proceeds[i]["image_file"] = pathlib.Path(file_name)

    for i, proceed in enumerate(proceeds[:3]):
        row = create_row(
            proceed["title"],
            proceed["image_file"],
            proceed["before_proceed"],
            proceed["after_proceed"],
            proceed["total"],
        )
        base.paste(row, (10, (row_height + 10) * i + 10))

    draw = ImageDraw.Draw(base)
    draw.text((10, 580), f"@{user_name}", (0, 0, 0), font=small_font, anchor="lt")
    draw.text(
        (10, 600),
        f"https://yondayo.vercel.app/{user_name}/{date_range}",
        (0, 0, 0),
        font=small_font,
        anchor="lt",
    )

    if len(proceeds) > 3:
        draw.text(
            (1150, 570), f"+{len(proceeds) - 3} 項目", (0, 0, 0), font=font, anchor="rt"
        )

    base.save("/tmp/out.png")

    # s3 = boto3.client("s3")  # S3オブジェクトを取得
    # s3.upload_file(
    #    "/tmp/out.png",
    #    "yondayo",
    #    f"ogp/{user_name}/{date_range}.png",
    #    ExtraArgs={"ACL": "public-read"},
    # )

    print("end")

    return {
        "statusCode": 200,
        "body": f"https://yondayo.vercel.app/{user_name}/{date_range}",
    }


if __name__ == "__main__":
    handler(
        {
            "body": json.dumps(
                {
                    "proceeds": [
                        {
                            "title": "BERTによる自然言語処理入門",
                            "image_url": "https://cover.openbd.jp/9784873119205.jpg",
                            "before_proceed": 90,
                            "after_proceed": 180,
                            "total": 180,
                        },
                        {
                            "title": "SVELTE TUTORIAL",
                            "image_url": "https://svelte.dev/images/twitter-card.png",
                            "before_proceed": 17,
                            "after_proceed": 18,
                            "total": 19,
                        },
                        {
                            "title": "データ解析のための数理モデル入門 本質を捉えた",
                            "image_url": "https://cover.openbd.jp/9784802612494.jpg",
                            "before_proceed": 106,
                            "after_proceed": 220,
                            "total": 273,
                        },
                        {
                            "title": "BERTによる自然言語処理入門",
                            "image_url": "https://cover.openbd.jp/9784873119205.jpg",
                            "before_proceed": 90,
                            "after_proceed": 180,
                            "total": 180,
                        },
                    ],
                    "user_name": "miyatsuki_shiku",
                    "date_range": "20210901-20210901",
                }
            )
        },
        "",
    )
