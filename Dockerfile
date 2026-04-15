FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

# Prevent python from writing pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IN_DOCKER=True

WORKDIR /app

# Install uv (blazing fast python package manager)
RUN pip install uv

# Copy project specification files first to cache layers
COPY pyproject.toml uv.lock ./

# Install python dependencies system-wide within the container
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application
COPY . .

# Run Playwright install to ensure chromium browsers are fully linked
RUN playwright install chromium
