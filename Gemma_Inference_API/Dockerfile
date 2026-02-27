FROM python:3.11-slim AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    python3-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# install deps into /install
COPY inference_requirments.txt .

RUN uv pip install --python /usr/local/bin/python --upgrade pip

RUN uv pip install --python /usr/local/bin/python --prefix=/install \
    sentence-transformers \
    --no-deps

RUN uv pip install --python /usr/local/bin/python --prefix=/install -r inference_requirments.txt

RUN uv pip install --python /usr/local/bin/python \
    --prefix=/install \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu126

FROM python:3.11-slim AS run

WORKDIR /inference_service

# copy installed deps from build stage
COPY --from=build /install /usr/local

# now copy only app code
COPY . .

ENV FLASK_ENV=development

EXPOSE 8081

CMD ["python", "run.py"]