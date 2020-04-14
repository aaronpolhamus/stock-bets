FROM ubuntu:18.04

# Operating system dependencies
# -----------------------------
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  gnupg \
  libev-dev \
  netcat \
  python3.7 \
  python3-pip \
  python3-setuptools \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.7 python \
  && rm -rf /var/lib/apt/lists/*

# Copy source and install python dependencies
# ------------------------------------

COPY . /home/stockbets
WORKDIR /home/stockbets
ENV PYTHONPATH="$PYTHONPATH:/home/stockbets/webapp"

# Install webapp-specific dependencies from repo
RUN python -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./docker-entrypoint.sh"]
