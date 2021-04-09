# GDAL -> PostGIS on AWS Lambda

Testing out AWS Lambda with GDAL's VSI Handlers. VSI handlers in GDAL allow for streaming data between commands and locations. A neat use case for these VSI handlers would be to wget/curl a file on the web, pipe the result through `ogr2ogr` and stream the content directly into a database without saving intermediate files.

Goal here is to get comfortable building lambda layers, comparing the result with either a single code layer (or the new ECS container-based layers), and have a function that writes a database file to S3 (or, if I spring for the NAT, to a DB!).

- [x] Create a few layers with the required utilities for:

  - [x] Geospatial processing (`GDAL`, `ogr2ogr`, etc.)
  - [x] Python dependencies (`boto3`, `awscli`, etc.)
  - [x] General utilities (`wget`)

- [ ] Look into writing a custom runtime (i.e. just a `bootsrtap.sh` file) which can use the layers from the above, and should  be quicker than filtering everything through `boto3` and `subprocess` calls in Python

## Building Layers

The layers used in this project are built in Amazon Linux Docker containers, see the content of `./layers/**` for details. Note that these layers are published independently of this project.

```bash
├── build_gdal.sh
├── build_psql.sh
├── build_python_deps.sh
└── build_utils.sh
```

```bash
# Build GDAL Layer - Contains Ogr2Ogr, GDAL, OgrInfo
# required for download handler
docker run --rm \
    --volume $(pwd)/built_layers/gdal:/gdal \
    --volume $(pwd)/layers/:/layers/ \
    remotepixel/amazonlinux-gdal \
    bash /layers/build_gdal.sh
```

```bash
# Build PSQL Layer - Contains PSQL
# required for restore layer
docker run --rm \
    --volume $(pwd)/built_layers/pgclient:/pgclient \
    --volume $(pwd)/layers/:/layers/ \
    amazonlinux \
    bash /layers/build_psql.sh
```

```bash
# Build wget Layer
# mostly didactic, required for download handler
docker run --rm \
    --volume $(pwd)/built_layers/utils:/utils \
    --volume $(pwd)/layers/:/layers/ \
    amazonlinux \
    bash /layers/build_utils.sh
```

```bash
# Build AWS Python deps Layer
# mostly didactic, required for both handlers, ideally using
# awscli, boto3 included for other runtimes...
docker run --rm \
    --volume $(pwd)/built_layers/pyutils:/pyutils \
    --volume $(pwd)/layers/:/layers/ \
    amazonlinux \
    bash /layers/build_python_deps.sh
```



## Testing Locally with Docker

## [WIP] Lambda Deployment

Depends on having an existing role, it is assumed this role has access to CloudWatch, S3, etc. Supplement `Variables` with required environment vars.

```bash
cd stg1_pgdump &&\ zip stg1_deployment.zip ./app.py

cd stg2_topg &&\ zip stg2_deployment.zip ./app.py

aws lambda create-function \
    --function-name loader \
    --zip-file fileb://stg1_deployment.zip \
    --handler app.handler \
    --runtime python3.8 \
    --timeout 30 \
    --role <YOUR ROLE ARN HERE> \
    --layers <YOUR LAYER ARNS HERE> \
    --environment "Variables={PROJ_DEBUG=3,PROJ_LIB=/opt/share/proj,GDAL_DATA=/opt/share/gdal}"
```

## References

- [Stack Overflow Post on VSI Handlers](https://gis.stackexchange.com/questions/122082/piping-data-to-ogr2ogr)
- [ogr2ogr VSI Docs](https://gdal.org/user/virtual_file_systems.html)
- Not used, prefer `remotepixel/amazonlinux-gdal` container [CentOS GDAL, ogr2ogr, proj Install Guide](9https://gist.github.com/abelcallejo/e75eb93d73db6f163b076d0232fc7d7e) 
- [Docker Container remotepixel/amazonlinux-gdal](https://hub.docker.com/r/remotepixel/amazonlinux-gdal)
- [DevelopmentSeed GeoLambda - Good Reference on Building Layers](https://github.com/developmentseed/geolambda/blob/master/bin/package.sh)


