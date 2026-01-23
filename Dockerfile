FROM python:3.13

RUN mkdir /app/
WORKDIR /app

COPY app/src/HemsServiceWorkshop app/src/HemsServiceWorkshop
COPY pyproject.toml app/
COPY README.md app/
RUN pip install ./

ENTRYPOINT python3 app/src/HemsServiceWorkshop/hemsserviceworkshop.py