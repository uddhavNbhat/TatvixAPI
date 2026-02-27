FROM python:3.12-slim

# Install uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory first
WORKDIR /file_service

# Copy only dependency metadata
COPY pyproject.toml uv.lock ./

# Install dependencies from lockfile into system Python
RUN uv pip install --system --no-cache .

# Create storage mount directory inside container
RUN mkdir /storage

# Now copy application source code
COPY . .

# Run service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8007"]