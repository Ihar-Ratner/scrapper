FROM ubuntu:24.04
# Install system dependencies
RUN apt-get update \
    && apt-get install -y wget unzip gnupg2 software-properties-common

# Install Python 3.13
RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update

RUN apt-get install python3.13 -y \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 \
    && apt-get install python3-pip -y

#RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Set up the XVFB server for running Chrome in headless mode
RUN apt-get install -y xvfb \
    && apt-get clean \
        && rm -rf /var/lib/apt/lists/* \
        && rm -rf /tmp/* \
        && rm -rf /var/tmp/*

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install

COPY . ./

# Create a startup script to properly initialize Xvfb
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &\n\
export DISPLAY=:99\n\
sleep 2\n\
exec "$@"' > /start.sh && chmod +x /start.sh

CMD ["/start.sh", "python3", "main.py"]

#CMD ["python3", "telegram_message.py"]


# Use Python 3.11 slim image
# FROM python:3.11-bullseye

# # Install system dependencies for Chrome
# RUN apt-get update && apt-get install -y \
#     wget \
#     gnupg \
#     unzip \
#     xvfb \
#     fonts-liberation \
#     libasound2 \
#     libatk-bridge2.0-0 \
#     libatk1.0-0 \
#     libatspi2.0-0 \
#     libcups2 \
#     libdbus-1-3 \
#     libdrm2 \
#     libgtk-3-0 \
#     libnspr4 \
#     libnss3 \
#     libxcomposite1 \
#     libxdamage1 \
#     libxrandr2 \
#     libxss1 \
#     libxtst6 \
#     xdg-utils \
#     && rm -rf /var/lib/apt/lists/*

# # Install Chrome
# RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
#     && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
#     && apt-get update \
#     && apt-get install -y google-chrome-stable \
#     && rm -rf /var/lib/apt/lists/*

# # Set up virtual display for headless Chrome
# ENV DISPLAY=:99

# # Create app directory
# WORKDIR /app

# # Copy requirements and install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# RUN playwright install

# # Copy application code
# COPY . .

# # Create necessary directories
# RUN mkdir -p cache logs

# # Create startup script
# RUN echo '#!/bin/bash\n\
# Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &\n\
# export DISPLAY=:99\n\
# sleep 2\n\
# exec "$@"' > /start.sh && chmod +x /start.sh

# # Expose port (if needed)
# EXPOSE 8000

# # Start virtual display and run the bot
# CMD ["/start.sh", "python", "main.py"]
