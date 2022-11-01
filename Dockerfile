FROM python:3.10-slim
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV PYTHONPATH /app
CMD ["python", "-u", "/app/bots/manage_events_bot.py"]