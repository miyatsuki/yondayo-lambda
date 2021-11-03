import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import autofill
import image
import proceed

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://yondayo-api.herokuapp.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get("/")
async def root():
    return {"message": "Hello World!!"}


@app.get("/proceed")
async def get_proceed(user_name: str, start_date: str, end_date: str):
    # TODO: timezoneの明示
    start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    proceeds, summary = proceed.handle(user_name, start_date, end_date)
    return {"proceed": proceeds, "summary": summary}


@app.get("/image")
async def get_image(user_name: str, start_date: str, end_date: str):
    # TODO: timezoneの明示
    start_date = datetime.datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.datetime.strptime(end_date, "%Y%m%d")
    url = image.handle(user_name, start_date, end_date)
    return {"url": url}


@app.get("/autofill")
async def get_autofill(url: str):
    info = autofill.handle(url)
    return info
