FROM python:3.12.3

WORKDIR /app

COPY requirements.txt .
COPY main.py .
COPY app/ ./app/

# Install system dependencies including libGL
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download it_core_news_sm
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download fr_core_news_sm
RUN python -m spacy download de_core_news_sm

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]