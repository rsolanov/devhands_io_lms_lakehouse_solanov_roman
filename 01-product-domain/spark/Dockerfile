# Используем официальный образ Apache Spark
FROM apache/spark:3.5.0-scala2.12-java11-python3-ubuntu

USER root

# ============================================================================
# Установка нативных библиотек Hadoop
# ============================================================================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libsnappy1v5 \
      libsnappy-dev \
      curl && \
    mkdir -p /opt/spark/lib/native && \
    echo "Downloading Hadoop 3.3.4 (663 MB)..." && \
    curl -fSL "https://archive.apache.org/dist/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz" \
      -o /tmp/hadoop.tar.gz && \
    echo "Extracting Hadoop..." && \
    tar -xzf /tmp/hadoop.tar.gz -C /tmp && \
    echo "Copying native libraries..." && \
    cp -r /tmp/hadoop-3.3.4/lib/native/* /opt/spark/lib/native/ && \
    echo "Cleaning up..." && \
    rm -rf /tmp/hadoop* && \
    chmod +x /opt/spark/lib/native/*.so* && \
    rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/opt/spark/lib/native:$LD_LIBRARY_PATH
ENV HADOOP_OPTS="-Djava.library.path=/opt/spark/lib/native"

# ============================================================================
# Установка JAR-файлов для Iceberg и S3
# ============================================================================
ARG HADOOP_AWS_VERSION=3.3.4
ARG ICEBERG_VERSION=1.5.0
ARG AWS_JAVA_SDK_VERSION=1.12.593

# curl УЖЕ установлен в предыдущем блоке, просто используем его
RUN curl -fSL "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar" \
      -o /opt/spark/jars/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar && \
    curl -fSL "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar" \
      -o /opt/spark/jars/iceberg-aws-bundle-${ICEBERG_VERSION}.jar && \
    curl -fSL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar" \
      -o /opt/spark/jars/hadoop-aws-${HADOOP_AWS_VERSION}.jar && \
    curl -fSL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-s3/${AWS_JAVA_SDK_VERSION}/aws-java-sdk-s3-${AWS_JAVA_SDK_VERSION}.jar" \
      -o /opt/spark/jars/aws-java-sdk-s3-${AWS_JAVA_SDK_VERSION}.jar

# ============================================================================
# Установка Python зависимостей
# ============================================================================
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      "pyiceberg[pyarrow]==0.7.1" \
      "s3fs==2023.12.2" \
      "fsspec==2023.12.2" \
      "urllib3>=1.25.4,<1.27" \
      "faker>=20.0.0" \
      "pandas>=2.0.0,<3.0.0"

# ============================================================================
# Копирование приложений
# ============================================================================
COPY ./applications /opt/spark/applications

USER spark
WORKDIR /opt/spark/work-dir