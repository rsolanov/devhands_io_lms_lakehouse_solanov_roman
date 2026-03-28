FROM trinodb/trino:435

USER root

RUN curl -fSL \
    "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/1.5.0/iceberg-aws-bundle-1.5.0.jar" \
    -o /usr/lib/trino/plugin/iceberg/iceberg-aws-bundle-1.5.0.jar

USER trino