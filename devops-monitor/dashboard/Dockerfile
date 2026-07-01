FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir \
    streamlit==1.58.0 \
    requests==2.34.2 \
    pandas==3.0.3

COPY dashboard/ dashboard/

ENV API_BASE_URL=http://api:8000
ENV API_KEY=dev-api-key

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
