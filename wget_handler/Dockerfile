# Boosted: https://pypi.org/project/awslambdaric/

# NOTE: Replacement for AWS Python Layer; Building from Source Instead of Deploying;
# Might find another way to ensure that layer is doing what it needs to!!
FROM public.ecr.aws/lambda/python:3.8

# for me, for debugging!
RUN  yum -y update &&\
  yum install -y unzip vim procps

RUN pip install boto3 awscli

COPY ./built_layers/gdal/lambda-gdal.zip ./built_layers/utils/lambda-deploy.zip /

# Need wget -> usr/bin/wget, will get missing *.so files if ldconfig not run to refresh
# libs
RUN cd / &&\
  unzip -o /lambda-gdal.zip &&\
  unzip -o /lambda-deploy.zip &&\
  /sbin/ldconfig
   
CMD ['handler.handler']
