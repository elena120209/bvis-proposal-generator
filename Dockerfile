FROM python:3.11-slim

# LibreOffice (Impress) for exact PPTX -> PDF conversion, plus fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-impress libreoffice-core fonts-liberation fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces runs the container as UID 1000; create that user
# so HOME is writable (LibreOffice needs a writable profile dir).
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860

WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user app.py filler.py template.pptx ./

EXPOSE 7860
CMD ["sh","-c","uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
