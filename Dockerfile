FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y\
        libttspico-utils\
        poppler-utils\
        tesseract-ocr-spa\
        python3\
        ffmpeg\
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY main.py ./

CMD python3 main.py
