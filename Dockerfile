FROM python:3.14

RUN mkdir /app/
WORKDIR /app

COPY src/HemsServiceWorkshop ./src/HemsServiceWorkshop
COPY pyproject.toml ./
COPY README.md ./

RUN pip install ./
ENTRYPOINT ["python3", "src/HemsServiceWorkshop/hems_service_workshop.py"]
