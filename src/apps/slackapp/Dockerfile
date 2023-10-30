# Use the official Python base image (Need bookworm for the latest sqlite)
FROM python:3.9-slim-bookworm

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential \
    && pip install --upgrade pip setuptools \
    && pip install hnswlib

ENV POETRY_HOME="/opt/poetry"

# Install Poetry
RUN pip install poetry

# Install pdfplumber
RUN pip install pdfplumber

# Copy the application code to the container
COPY . .

# Install the Python dependencies for slackapp
RUN cd apps/slackapp && poetry install

# Expose the port that the Flask app will listen on
EXPOSE 80


# Set the working directory in the container
WORKDIR /app/apps/slackapp
# Run the Flask app
CMD ["poetry", "run", "python", "-m", "slackapp.bolt_app"]
