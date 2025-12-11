FROM python:3.9-alpine

WORKDIR /app

# Install build dependencies for Pandas/Numpy/Streamlit
# libstdc++ is needed for pandas runtime
RUN apk add --no-cache libstdc++ && \
    apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    make \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

COPY requirements.txt .

# Install Python dependencies
# This might take a while on Alpine as it compiles from source
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to keep image small
RUN apk del .build-deps

# Copy application code
COPY .streamlit /root/.streamlit
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the dashboard
CMD ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
