FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home mambot && mkdir -p /app/var && chown -R mambot:mambot /app
USER mambot
ENV MAMBOT_HOST=0.0.0.0 PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "run.py"]
