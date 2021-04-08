#!/bin/sh

# Build a wget Lambda Layer: Built on Amazon Linux

# docker run -ti \
#   --volume $(pwd)/pyutils:/pyutils \
#   --volume $(pwd)/layers/:/layers/ \
#   amazonlinux bash -c '/layers/build_python_deps.sh'
# 

# Using the AWS AMI specific `amazon-linux-extras` -> Install Python3 w. pip
amazon-linux-extras install python3 epel -y
    
yum -y update &&\
    yum install zip -y &&\
    yum groupinstall -y "Development Tools"

# Install Pip
curl -O "https://bootstrap.pypa.io/get-pip.py" &&\
    python3 get-pip.py --user
    
# Pip Install
python3 -m pip install boto3 awscli --target /pyutils_stg/bin/ --upgrade &&\
    mkdir -p /pyutils_stg/bin &&\
    cd /pyutils_stg &&\
    zip /pyutils/aws-python-layer.zip -r ./
