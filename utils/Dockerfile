FROM python:3.12-slim-bookworm

WORKDIR /bot

COPY /utils/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY /src/ .

CMD ["python3", "GarageBot.py"]
