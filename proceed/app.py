import datetime
import json
import os
from typing import Dict, NamedTuple
from supabase import create_client, Client


class ProceedLog(NamedTuple):
    book_id: int
    title: str
    url: str
    image_url: str
    before_proceed: int
    after_proceed: int
    total: int
    created_at: datetime.datetime


def default(o):
    if hasattr(o, "isoformat"):
        return o.isoformat()
    else:
        return str(o)


def handler(event, context):
    print(event)
    data = event["queryStringParameters"]
    user_name = data["user_name"]
    start_date = datetime.datetime.strptime(data["date_range"].split("-")[0], "%Y%m%d")
    end_date = datetime.datetime.strptime(data["date_range"].split("-")[1], "%Y%m%d")

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    data = (
        supabase.table("users").select("user_id").eq("user_name", user_name).execute()
    )
    user_id = data["data"][0]["user_id"]
    data = (
        supabase.table("proceed_log")
        .select(
            "after_proceed, before_proceed, book_id, created_at, image_url, title, total, url"
        )
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
        if proceed["before_proceed"] != proceed["after_proceed"]
    ]

    recent_proceed: Dict[int, ProceedLog] = {}
    first_proceed: Dict[int, ProceedLog] = {}
    for proceed in proceeds:
        if proceed.book_id in recent_proceed:
            if proceed.created_at > recent_proceed[proceed.book_id].created_at:
                recent_proceed[proceed.book_id] = proceed
        else:
            recent_proceed[proceed.book_id] = proceed

        if proceed.book_id in first_proceed:
            if proceed.created_at < first_proceed[proceed.book_id].created_at:
                recent_proceed[proceed.book_id] = proceed
        else:
            first_proceed[proceed.book_id] = proceed

    summary = {
        book_id: {
            "title": recent_proceed[book_id].title,
            "inital": first_proceed[book_id].before_proceed,
            "total": recent_proceed[book_id].total,
        }
        for book_id in recent_proceed
    }

    return {
        "statusCode": 200,
        "body": json.dumps({"proceeds": proceeds, "summary": summary}, default=default),
    }


if __name__ == "__main__":
    handler(
        {
            "body": json.dumps(
                {
                    "user_name": "miyatsuki_shiku",
                    "start_date": "2021-10-01",
                    "end_date": "2021-10-31",
                }
            )
        },
        "",
    )
