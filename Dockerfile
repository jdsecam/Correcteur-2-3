# Utiliser une image Debian légère avec Python
FROM python:3.11-slim

# Installer gcc et make
RUN apt-get update && apt-get install -y gcc make && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier les fichiers
COPY requirements.txt .
COPY app_streamlit_correcteur_full.py .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port utilisé par Streamlit
EXPOSE 8501

# Lancer Streamlit
CMD ["streamlit", "run", "app_streamlit_correcteur_full.py", "--server.port=8501", "--server.address=0.0.0.0"]
