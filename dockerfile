# Use an official Ubuntu runtime as a parent image
FROM ubuntu:20.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, Python, and Firefox
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    software-properties-common \
    python3 \
    python3-pip \
    && add-apt-repository ppa:mozillateam/ppa \
    && apt-get update \
    && apt-get install -y firefox \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install GeckoDriver
RUN GECKO_DRIVER_VERSION=$(curl -sS https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f 4) \
    && wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/$GECKO_DRIVER_VERSION/geckodriver-$GECKO_DRIVER_VERSION-linux64.tar.gz \
    && tar -C /usr/local/bin -zxf /tmp/geckodriver.tar.gz \
    && rm /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

# Copy the current directory contents into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV FIREFOX_BINARY=/usr/bin/firefox

# Run app.py when the container launches
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
