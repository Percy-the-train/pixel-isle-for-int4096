FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV NCB_HOST=0.0.0.0 NCB_NO_BROWSER=1 NCB_DATA_DIR=/data
EXPOSE 8765
CMD ["python", "run.py"]