FROM python:3.9-alpine
LABEL authors="german.garces@appfire.com"

# Install required Python packages
RUN pip install --no-cache-dir c7n-org==0.6.42 c7n-mailer==0.6.42

ENTRYPOINT ["top", "-b"]