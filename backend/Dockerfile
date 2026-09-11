FROM python:3.12

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./req.txt ./requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

COPY ./backend ./backend
COPY ./main.py ./main.py
COPY ./alembic.ini ./alembic.ini
COPY ./migrations ./migrations
COPY ./entrypoint.sh ./entrypoint.sh

RUN sed -i 's/\r$//' ./entrypoint.sh && chmod +x ./entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["uvicorn","main:duolingo","--host","0.0.0.0","--port","8000"]