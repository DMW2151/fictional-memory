# Boosted: https://pypi.org/project/awslambdaric/

# Define custom function directory
FROM amazonlinux

ARG FUNCTION_DIR="/function"

# Add Python3.8 to the Image
RUN amazon-linux-extras install python3 epel -y &&\
  yum -y update &&\
  yum install zip -y &&\
  yum groupinstall -y "Development Tools" &&\
  curl -O "https://bootstrap.pypa.io/get-pip.py" &&\
  python3 get-pip.py

# Copy handler function
COPY ./wget_handler/ ${FUNCTION_DIR}/

COPY ./built_layers/gdal/lambda-gdal.zip ./built_layers/pyutils/aws-python-layer.zip ./built_layers/utils/lambda-deploy.zip  ./

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "app.handler" ]