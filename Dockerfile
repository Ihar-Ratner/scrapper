# Use an official Python runtime as a base image
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update \
    && apt-get install -y wget unzip gnupg2

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Additional configuration to allow Chrome to run in headless mode
ENV DISPLAY=:99

# Set up the XVFB server for running Chrome in headless mode
RUN apt-get install -y xvfb
RUN Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &

# Set the working directory in the container
WORKDIR /app

# Copy the Python script and requirements file to the container
COPY wb_scrapper.py requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the Python script
CMD ["xvfb-run", "python", "wb_scrapper.py"]
