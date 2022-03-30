# Use a Python 3.9 slim image
FROM python:3.10.2-slim

RUN apk update && apk add python3-dev \
                          gcc \
                          libc-dev \
                          libffi-dev

# Create and set the 'app' working directory
RUN mkdir /app
WORKDIR /app

# Copy repository contents into the working directory
COPY . /app

# Upgrade pip and install dependencies
RUN python setup.py install

# Set entrypoint
ENTRYPOINT ["tag-bot"]
