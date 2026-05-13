FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/

# 将 docs 打包到镜像内作为备用（/app/docs_baked/）
# 若 ./docs 挂载卷不可用或为空，sync_exams 会自动回退到此目录
COPY docs/ ./docs_baked/

# SQLite 数据目录（由 volume 挂载）
RUN mkdir -p /app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
