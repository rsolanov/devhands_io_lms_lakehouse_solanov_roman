FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    dbt-trino==1.10.1 \
    keyring

WORKDIR /usr/app/dbt

COPY dbt_project/ .
COPY profiles.yml /root/.dbt/profiles.yml

CMD ["tail", "-f", "/dev/null"]