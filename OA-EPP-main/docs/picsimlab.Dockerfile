# Example Dockerfile template for PicSimLab
# If there is no official image, place build steps here and let Coolify build from repo.
# Replace the following with actual build/install steps for PicSimLab.
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
# RUN apt-get update && apt-get install -y \ 
#     build-essential \ 
#     libffi-dev \ 
#     && rm -rf /var/lib/apt/lists/*

# Copy application source (if building from source)
# COPY . /app

# Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# Expose the web UI port (adjust if different)
EXPOSE 8080

# Default command - replace with the actual startup command
CMD ["python", "run_picsimlab.py"]
