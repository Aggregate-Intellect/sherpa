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


# Copy the application code to the container
COPY . .

# Install dependency of Sherpa
RUN poetry install

# Install the Python dependencies for slackapp
RUN cd apps/slackapp && poetry install

# Download the spaCy trained pipeline for English
RUN python -m spacy download en_core_web_sm

# Expose the port that the Flask app will listen on
EXPOSE 80


# Set the working directory in the container
WORKDIR /app/apps/slackapp
# Run the Flask app
CMD ["poetry", "run", "python", "-m", "slackapp.bolt_app"]
