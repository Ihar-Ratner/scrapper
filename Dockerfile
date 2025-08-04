FROM ubuntu:22.04
# Install system dependencies
RUN apt-get update \
    && apt-get install -y wget unzip gnupg2 python3-pip

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Set up the XVFB server for running Chrome in headless mode
RUN apt-get install -y xvfb

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt
RUN playwright install

COPY . ./

# Create a startup script to properly initialize Xvfb
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &\n\
export DISPLAY=:99\n\
sleep 2\n\
exec "$@"' > /start.sh && chmod +x /start.sh

CMD ["/start.sh", "python3", "telegram_message.py"]

#CMD ["python3", "telegram_message.py"]
