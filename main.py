from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import sqlite3
import os
import time
import threading

app = FastAPI(title="FastAPI SQLite Observability App")


DB_PATH = os.getenv("DB_PATH", "/data/app.db")
APP_VERSION = os.getenv("APP_VERSION", "v1")
START_TIME = time.time()



HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"],
    buckets=(0.1, 0.3, 0.5, 1, 2, 5)
)

APP_UPTIME_SECONDS = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds"
)

APP_INFO = Gauge(
    "app_info",
    "Application version info",
    ["version"]
)

DB_ERRORS_TOTAL = Counter(
    "db_errors_total",
    "Total database errors"
)

APP_INFO.labels(version=APP_VERSION).set(1)


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )
    return conn

conn = get_conn()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    HTTP_REQUESTS_TOTAL.labels(
        request.method,
        request.url.path,
        response.status_code,
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        request.url.path
    ).observe(duration)

    return response


def update_uptime():
    while True:
        APP_UPTIME_SECONDS.set(time.time() - START_TIME)
        time.sleep(5)

threading.Thread(target=update_uptime, daemon=True).start()


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": APP_VERSION}

@app.put("/item/{item_id}")
def put_item(item_id: int, value: str):
    try:
        conn.execute(
            """
            INSERT INTO items (id, value)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET value=?
            """,
            (item_id, value, value)
        )
        conn.commit()
        return {"message": "Item stored", "id": item_id, "value": value}
    except Exception:
        DB_ERRORS_TOTAL.inc()
        return Response(
            content='{"error":"db error"}',
            status_code=500,
            media_type="application/json"
        )

@app.get("/item/{item_id}")
def get_item(item_id: int):
    try:
        cursor = conn.execute(
            "SELECT value FROM items WHERE id = ?",
            (item_id,)
        )
        row = cursor.fetchone()
        if not row:
            return {"message": "Item not found"}
        return {"id": item_id, "value": row[0]}
    except Exception:
        DB_ERRORS_TOTAL.inc()
        return Response(
            content='{"error":"db error"}',
            status_code=500,
            media_type="application/json"
        )
