FROM python:3.9
LABEL authors="german.garces@appfire.com"

ENV ROLE_ARN="arn:aws:iam::891377226793:role/AppfireCloudCustodian"
ENV AWS_REGION="us-east-2"

COPY scripts /app/scripts
COPY config /app/config
COPY entrypoint.sh /app/entrypoint.sh

ADD https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip awscliv2.zip

RUN apt-get update && \
    apt-get install --no-install-recommends -y gettext=0.21-* && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip && \
    pip install --no-cache-dir -r /app/config/requirements.txt && \
    chmod +x /app/entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh", "--verbose"]
CMD ["/bin/bash", "/app/scripts/c7n-pipeline.sh", "--verbose"]