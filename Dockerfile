FROM centos:centos8

ENV USERMAP_UID 1000
ENV HOME /home/ssl_expire_script
ENV AWS_DEFAULT_REGION   eu-west-2
ENV GET_EXPIRY_COMMAND   'openssl x509 -enddate -noout -in /home/ssl_expire_script/fms-certificate.pem'


RUN yum update -y --quiet \
    && yum install python3 -y \
    && yum install openssl -y \
    && yum install zip -y \
    && curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' \
    && unzip awscliv2.zip \
    && ./aws/install \
    && pip3 install boto3

RUN mkdir -p '/home/ssl_expire_script'

# Add user
RUN groupadd -r runner && \
    useradd --no-log-init -u $USERMAP_UID -r -g runner runner && \
    groupadd docker && \
    usermod -aG docker runner && \
    chown -R runner:runner /home/ssl_expire_script

COPY 'scripts/cert_expiry_monitor.py' '/home/ssl_expire_script'

USER ${USERMAP_UID}

WORKDIR /home/ssl_expire_script

CMD tail -f /dev/null
