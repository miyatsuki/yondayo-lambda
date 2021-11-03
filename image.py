import datetime
import os
import pathlib
from typing import Dict, NamedTuple
import boto3
import requests
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont

font_file = os.environ["FONT_FILE"]
if not os.exists(font_file):
    s3 = boto3.resource("s3")
    s3.Bucket("yondayo").download_file(Filename=font_file, Key=f"assets/{font_file}")

font = ImageFont.truetype(font_file, 40)
small_font = ImageFont.truetype(font_file, 20)

row_height = 180


class ProceedLog(NamedTuple):
    book_id: int
    title: str
    url: str
    image_url: str
    before_proceed: int
    after_proceed: int
    total: int
    created_at: datetime.datetime


def create_row(
    title: str,
    image_file: pathlib.Path,
    before_proceed: int,
    after_proceed: int,
    total: int,
):
    row = Image.new("RGB", (1200, row_height), (256, 256, 256))

    if image_file:
        image = Image.open(image_file)
        width, height = image.size

        scale_h = row_height / height
        scale_w = 200 / width
        scale = min(scale_h, scale_w)

        resized_size = (int(width * scale), int(height * scale))
        image_resized = image.resize(resized_size)
        width, height = image_resized.size

        row.paste(
            image_resized, (int((200 - width) / 2), int((row_height - height) / 2))
        )

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


def handle(user_name: str, start_date: datetime.date, end_date: datetime.date):
    date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    data = (
        supabase.table("users").select("user_id").eq("user_name", user_name).execute()
    )
    user_id = data["data"][0]["user_id"]
    data = (
        supabase.table("proceed_log")
        .select("*")
        .eq("user_id", user_id)
        .gte("created_at", (start_date + datetime.timedelta(hours=-9)).isoformat())
        .lt("created_at", (end_date + datetime.timedelta(hours=-9)).isoformat())
        .execute()
    )
    proceeds = [
        ProceedLog(
            proceed["book_id"],
            proceed["title"],
            proceed["url"],
            proceed["image_url"],
            proceed["before_proceed"],
            proceed["after_proceed"],
            proceed["total"],
            datetime.datetime.fromisoformat(proceed["created_at"].split(".")[0]),
        )
        for proceed in data["data"]
    ]

    oldest_proceed: Dict[int, ProceedLog] = {}
    recent_proceed: Dict[int, ProceedLog] = {}
    for proceed in proceeds:
        if proceed.book_id in oldest_proceed:
            if proceed.created_at < oldest_proceed[proceed.book_id].created_at:
                oldest_proceed[proceed.book_id] = proceed
        else:
            oldest_proceed[proceed.book_id] = proceed

        if proceed.book_id in recent_proceed:
            if proceed.created_at > recent_proceed[proceed.book_id].created_at:
                recent_proceed[proceed.book_id] = proceed
        else:
            recent_proceed[proceed.book_id] = proceed

    proceed_diff = [
        ProceedLog(
            book_id,
            proceed.title,
            proceed.url,
            proceed.image_url,
            oldest_proceed[book_id].before_proceed,
            proceed.after_proceed,
            proceed.total,
            proceed.created_at,
        )
        for book_id, proceed in recent_proceed.items()
    ]
    print(proceed_diff)

    # 進捗があったものだけに絞る
    proceed_diff = [
        proceed
        for proceed in proceed_diff
        if proceed.after_proceed - proceed.before_proceed > 0 and proceed.total > 0
    ]
    proceed_diff = sorted(
        proceed_diff,
        reverse=True,
        key=lambda x: (x.after_proceed - x.before_proceed) / x.total,
    )

    size = (1200, 630)
    base = Image.new("RGB", size, (256, 256, 256))

    image_files = []
    for i, proceed in enumerate(proceed_diff):
        if proceed.image_url != "":
            r = requests.get(proceed.image_url)
            suffix = proceed.image_url.split(".")[-1]
            file_name = f"/tmp/{i}.{suffix}"
            with open(file_name, "wb") as f:
                f.write(r.content)
            image_files.append(pathlib.Path(file_name))
        else:
            image_files.append(None)

    for i, proceed in enumerate(proceed_diff[:3]):
        row = create_row(
            proceed.title,
            image_files[i],
            proceed.before_proceed,
            proceed.after_proceed,
            proceed.total,
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

    if len(proceed_diff) > 3:
        draw.text(
            (1150, 570),
            f"+{len(proceed_diff) - 3} 項目",
            (0, 0, 0),
            font=font,
            anchor="rt",
        )

    base.save("/tmp/out.png")

    s3 = boto3.client("s3")  # S3オブジェクトを取得
    s3.upload_file(
        "/tmp/out.png",
        "yondayo",
        f"ogp/{user_name}/{date_range}.png",
        ExtraArgs={"ACL": "public-read"},
    )

    print("end")

    return f"https://yondayo.vercel.app/{user_name}/{date_range}"
