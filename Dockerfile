FROM python:3.10-slim
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
ENV PYTHONPATH /app
ENV UPDATE_SIDEBAR True
ENV THREAD_STATS True
ENV IN_PLAYOFFS False
ENV PLAYOFF_WATCH False
CMD ["python", "/app/bots/manage_events_bot.py"]