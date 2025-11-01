# Use a Python slim image
FROM python:3.14.0-slim

# Install gcc and wget
RUN apt-get update && apt-get install --yes gcc wget

# Install yq
RUN wget https://github.com/mikefarah/yq/releases/download/v4.25.2/yq_linux_amd64.tar.gz -O - | \
  tar xz && mv yq_linux_amd64 /usr/bin/yq

# Create and set the 'app' working directory
RUN mkdir /app
WORKDIR /app

# Copy repository contents into the working directory
COPY . /app

# Upgrade pip and install dependencies
RUN pip install -U pip
RUN pip install .

# Set entrypoint
ENTRYPOINT ["tag-bot"]
