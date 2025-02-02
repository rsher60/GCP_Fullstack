FROM python:3.10-slim

WORKDIR /app
EXPOSE 5880
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["fastapi","run","main.py","--port","5880"]