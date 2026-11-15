FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg tini && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd -g 10001 monitor && useradd -u 10001 -g monitor -M monitor && mkdir /data /recordings /cache && chown monitor:monitor /data /recordings /cache
COPY app ./app
COPY static ./static
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "app.server"]
