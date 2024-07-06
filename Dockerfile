FROM python:3.9-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
EXPOSE 8501
ENTRYPOINT ["streamlit", "run" , "main.py", "--server.port=8501", "server.address=127.0.0.1"]