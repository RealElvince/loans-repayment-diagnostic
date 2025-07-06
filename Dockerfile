FROM python:3.11-slim

# Create and set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app files
COPY . .

# Use Gunicorn to run your app in production:
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
