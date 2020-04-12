FROM ubuntu:18.04

# System dependencies
# -------------------
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  gnupg \
  libev-dev \
  python3.7 \
  python3-pip \
  python3-setuptools \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.7 python \
  && rm -rf /var/lib/apt/lists/*

# 3. Copy source and install dependencies
# ---------------------------------------

COPY ./backend /home/backend
COPY ./db /home/db
WORKDIR /home/backend

# Install backend-specific dependencies from repo
RUN python -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python"]
CMD ["app.py"]