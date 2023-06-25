# Use the official Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file
COPY requirements.txt .


RUN apt-get update && apt-get install -y build-essential \
    && pip install --upgrade pip setuptools \
    && pip install hnswlib
# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose the port that the Flask app will listen on
EXPOSE 80

# Run the Flask app
CMD ["python", "app.py"]
