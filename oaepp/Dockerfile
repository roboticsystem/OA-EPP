FROM python:3.11-slim

WORKDIR /app
COPY oaepp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY oaepp/ ./oaepp/
COPY oaepp/assets/ ./assets/

EXPOSE 3000 8000
CMD ["reflex", "run", "--env", "prod"]
