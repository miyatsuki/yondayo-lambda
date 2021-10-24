import json
from bs4 import BeautifulSoup
import requests


def parse_head(url: str):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, "html.parser")

    title = soup.title.get_text()
    image_url = None
    for tag in soup.find_all("meta"):
        if "property" in tag.attrs and tag["property"] == "og:image":
            image_url = tag["content"]

    return {"url": url, "title": title, "imageURL": image_url}


def handler(event, context):
    print(event)
    payload = event["body"]
    print(payload)
    data = json.loads(payload)

    info = parse_head(data["url"])
    return {"statusCode": 200, "body": json.dumps(info)}


if __name__ == "__main__":
    handler("", "")
