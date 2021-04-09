# Boosted: https://pypi.org/project/awslambdaric/
# Boosted: https://trac.osgeo.org/gdal/wiki/BuildingOnUnixWithMinimizedDrivers

# Stage 1 - Build

# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM python:3.8-buster as build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR


# # Install aws-lambda-cpp build dependencies
# https://mothergeo-py.readthedocs.io/en/latest/development/how-to/gdal-ubuntu-pkg.html
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  build-essential \
  libproj-dev \
  proj-bin \
  proj-data \
  gdal-bin \
  libgdal-dev \
  libcurl4-openssl-dev

# Instead of building GDAL from source w. all drivers, or getting the full gzipped
# distribution, only build the PGDdriver
RUN wget https://github.com/OSGeo/gdal/releases/download/v3.2.1/gdal-3.2.1.tar.gz &&\ 
    gunzip gdal-3.2.1.tar.gz 

# Install GEOS - Required for CartoPy
RUN wget http://download.osgeo.org/geos/geos-3.9.1.tar.bz2 &&\
    bzip2 -d geos-3.9.1.tar.bz2

RUN mkdir -p ${FUNCTION_DIR}

# Copy handler function
COPY app/ ${FUNCTION_DIR}/

RUN pip install -U pip \
   && pip install -r ${FUNCTION_DIR}/requirements/dev.txt

# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "app.handler" ]