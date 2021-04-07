#! bin/sh

# Build a GDAL + OGR2OGR Lambda Layer: Built on Amazon Linux using remotepixel/amazonlinux-gdal
# which contains the required utilities pre-instealled instead of building the binaries from source
# docker run -ti --volume $(pwd)/gdal:/gdal remotepixel/amazonlinux-gdal bash -c './layers /build_gdal.sh'

# Copy GDAL, OGR2OGR, and OGRINFO Binaries -> /gdal/bin
mkdir -p /gdal/bin /gdal/lib /gdal/share &&\
    cp /var/task/bin/gdalinfo /gdal/bin/ &&\
    cp /var/task/bin/ogrinfo /gdal/bin/ &&\
    cp /var/task/bin/ogr2ogr /gdal/bin/

# Copy Shared Libs -> /gdal/lib
ldd /var/task/bin/gdalinfo |\
    grep "=> /" |\
    awk '{print $3}' |\
    xargs -I '{}' cp -v '{}' /gdal/lib/

ldd /var/task/bin/ogrinfo |\
    grep "=> /" |\
    awk '{print $3}' |\
    xargs -I '{}' cp -v '{}' /gdal/lib/

ldd /var/task/bin/proj |\
    grep "=> /" |\
    awk '{print $3}' |\
    xargs -I '{}' cp -v '{}' /gdal/lib/

ldd /var/task/bin/ogr2ogr |\
    grep "=> /" |\
    awk '{print $3}' |\
    xargs -I '{}' cp -v '{}' /gdal/lib/

# Rsync the Share Files 
rsync -ax /var/task/share/gdal /gdal/share/
rsync -ax /var/task/share/proj /gdal/share/

strip /gdal/lib/* || true

cd /gdal/ &&\ 
    zip --symlinks -ruq lambda-gdal.zip ./
```
