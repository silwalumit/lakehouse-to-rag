# Use official Python image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements for caching
COPY ./scraper/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy scraper source code into container
COPY ./scraper /app/scraper

# Copy shared src folder if needed (adjust path)
COPY ./helpers /app/helpers
COPY ./config /app/config

# Default command is to run your scraper CLI (can be overridden)
ENTRYPOINT ["python", "-m", "scraper"]
