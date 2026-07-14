web: gunicorn app:fapp -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:${PORT:-10000}
