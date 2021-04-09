# Boosted: https://pypi.org/project/awslambdaric/

# Define custom function directory
FROM python:3.8-buster as build-image

ARG FUNCTION_DIR="/function"

# Copy handler function
COPY pg_restore_handler/ ${FUNCTION_DIR}/

COPY built_layers/gdal/lambda-gdal.zip \
  built_layers/pyutils/aws-python-layer.zip \
  built_layers/utils/lambda-deploy.zip  ./

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "app.handler" ]