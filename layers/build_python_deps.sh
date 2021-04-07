# Build a wget Lambda Layer: Built on Amazon Linux
# docker run -ti --volume $(pwd)/pyutils:/pyutils amazonlinux bash -c './layers/build_python_deps.sh'

# Using the AWS AMI specific `amazon-linux-extras` -> Install Python3 w. pip
amazon-linux-extras install python3 epel -y
    
yum -y update &&\
    yum install -y wget &&\
    yum groupinstall -y "Development Tools"

# Pip Install
pip install boto3 awscli --target pyutils/. &&\
    zip boto3-layer.zip -r pyutils/
