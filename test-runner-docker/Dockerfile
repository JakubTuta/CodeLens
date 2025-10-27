FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache docker-cli

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV PORT=8001

EXPOSE $PORT

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"
