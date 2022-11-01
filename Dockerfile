FROM python:3.10-slim
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
ENV PYTHONPATH /app
CMD ["python", "/app/bots/manage_events_bot.py"]