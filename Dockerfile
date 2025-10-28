FROM python:3.11-bullseye

# Installer gcc et make
RUN apt-get update && apt-get install -y gcc make && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
COPY app_streamlit_correcteur_full.py .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app_streamlit_correcteur_full.py", "--server.port=8501", "--server.address=0.0.0.0"]
