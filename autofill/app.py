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


def fetch_openBD_info(isbn10: str):
    r = requests.get(f"https://api.openbd.jp/v1/get?isbn={isbn10}")
    data = r.json()

    title = data[0]["summary"]["title"]
    imageURL = data[0]["summary"]["cover"]
    total = data[0]["onix"]["DescriptiveDetail"]["Extent"][0]["ExtentValue"]

    return {"title": title, "imageURL": imageURL, "total": total}


def is_isbn(code: str):
    # 全部数字ならISBNとみなす
    if code.isdigit():
        return True
    # 最終桁以外数字で最後がXの場合はISBNとみなす
    elif code[:-1].isdigit() and code[-1] == "X":
        return True
    else:
        return False


def handler(event, context):
    print(event)
    payload = event["body"]
    print(payload)
    data = json.loads(payload)
    url: str = data["url"]

    info = {}
    if url.startswith("https://www.amazon.co.jp/"):
        path = url.split("/")
        isbn = ""
        for i in range(1, len(path)):
            if path[i - 1] == "dp" and is_isbn(path[i]):
                isbn = path[i]
                break
        if isbn:
            info = fetch_openBD_info(isbn)
            info["url"] = url
    if not isbn:
        info = parse_head(url)

    return {"statusCode": 200, "body": json.dumps(info)}


if __name__ == "__main__":
    handler("", "")
