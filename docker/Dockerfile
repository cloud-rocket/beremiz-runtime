# Use Python 3.11 as base image
FROM python:3.11-slim-buster
LABEL maintainer="opensource@imubit.com"
LABEL maintainer_name="Meir Tseitlin (Imubit)"

# Copy the current directory contents into the container at /app
ADD . /app

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
RUN python3 -m pip install --no-cache-dir -e . \
    && rm -rf /var/lib/apt/lists/*

# Command to run the Python script
CMD ["br-runtime-cli"]
