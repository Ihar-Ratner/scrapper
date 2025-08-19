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
