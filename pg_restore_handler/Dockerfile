# Boosted: https://pypi.org/project/awslambdaric/

# Define custom function directory
FROM public.ecr.aws/lambda/python:3.8

# for me, for debugging!
RUN  yum -y update &&\
  yum install -y \
    unzip \
    vim \
    procps

RUN pip install boto3 awscli

COPY ./built_layers/pgclient/lambda-psql.zip ./built_layers/pyutils/aws-python-layer.zip /

# Need wget -> usr/bin/wget, will get missing *.so files if ldconfig not run to refresh
# libs
RUN cd / &&\
  unzip -o /lambda-psql.zip &&\
  unzip -o /aws-python-layer.zip &&\
  /sbin/ldconfig
   
CMD ['handler.handler']
