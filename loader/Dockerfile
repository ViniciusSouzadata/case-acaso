FROM python:3.12-slim
WORKDIR /app
COPY loader/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY loader/ /app/loader/
COPY analise/ /app/analise/
CMD ["python", "-m", "loader.cli"]
