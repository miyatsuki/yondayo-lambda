FROM public.ecr.aws/lambda/python:3.9
# FROM python:buster
RUN pip install -U --no-cache-dir pip wheel setuptools
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
CMD ["app.handler"]
