FROM ubuntu:18.04

# Operating system dependencies
# -----------------------------
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  unzip \
  gnupg \
  libev-dev \
  netcat \
  python3.7 \
  python3-pip \
  python3-setuptools \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.7 python \
  && rm -rf /var/lib/apt/lists/*

# Copy source files to container and set working directory
# --------------------------------------------------------
COPY . /home/backend
WORKDIR /home/backend
ENV PYTHONPATH="$PYTHONPATH:/home"

# Copy source and install python dependencies
# -------------------------------------------
RUN python -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./docker/backend-entrypoint.sh"]
