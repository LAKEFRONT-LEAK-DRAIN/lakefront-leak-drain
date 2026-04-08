FROM python:3.11-slim

WORKDIR /app

COPY requirements-bridge.txt ./
RUN pip install --no-cache-dir -r requirements-bridge.txt

COPY pending_tasks_bridge.py ./

ENV PORT=8080

CMD ["python", "pending_tasks_bridge.py"]
