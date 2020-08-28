FROM ubuntu:18.04

# Operating system dependencies
# -----------------------------
RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends \
  build-essential \
  groff \
  curl \
  unzip \
  gnupg \
  libev-dev \
  firefox \
  mysql-client \
  chromium-chromedriver \
  netcat \
  python3.7 \
  python3-pip \
  python3-setuptools \
  python3.7-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.7 python \
  && rm -rf /var/lib/apt/lists/*

# Copy source files to container and set working directory
# --------------------------------------------------------
COPY . /home/backend
WORKDIR /home/backend
ENV PYTHONPATH="$PYTHONPATH:/home"

# Install geckodriver for webscraping with selenium + firefox
# -----------------------------------------------------------
RUN curl -OL https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz \
    && tar -xvzf geckodriver* \
    && chmod +x geckodriver \
    && rm *tar.gz \
    && export PATH=$PATH:/home/backend/geckodriver/.

# Copy source and install python dependencies
# -------------------------------------------
RUN python -m pip install -r requirements.txt

ENTRYPOINT ["./docker/backend-entrypoint.sh"]
