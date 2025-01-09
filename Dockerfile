# 1. Use an official Python runtime as a parent image
FROM python:3.9

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements.txt first (for caching)
COPY requirements.txt /app/

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the app code into the container
COPY . /app

# 6. Expose port 8050 (optional for local reference; not strictly needed for Cloud Run)
EXPOSE 8080

# 7. Specify the command to start the app
#    We'll use gunicorn to serve the Dash app in production
CMD ["python", "app.py"]
