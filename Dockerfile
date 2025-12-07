FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/produk uploads/bukti_pembayaran uploads/ktp

EXPOSE 5000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120