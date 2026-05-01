FROM python:3.11-slim

WORKDIR /app

# Önce bağımlılıkları kur (cache'den faydalanmak için ayrı adım)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sadece uygulama kodunu kopyala
# .env KOPYALANMIYOR — runtime'da env_file ile okunuyor
COPY vasi.py .

CMD ["python", "vasi.py"]
