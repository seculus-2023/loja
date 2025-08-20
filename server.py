from waitress import serve
from core.wsgi import application

if __name__ == "__main__":
    # 127.0.0.1 porque o Nginx faz o proxy; não exponha publicamente
    serve(
        application,
        listen="127.0.0.1:8000",
        threads=6,
        connection_limit=200,
        channel_timeout=120
    )
