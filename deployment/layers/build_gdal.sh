#! bin/sh

# Build a GDAL + OGR2OGR Lambda Layer: Built on Amazon Linux using remotepixel/amazonlinux-gdal
# which contains the required utilities pre-instealled instead of building the binaries from source

yum upgrade -y &&\
    yum install -y binutils zip

# Copy GDAL, OGR2OGR, and OGRINFO Binaries -> /gdal/bin && some optional bins
mkdir -p /gdal/bin /gdal/lib /gdal/share &&\
    cp /var/task/bin/gdalinfo \
    /var/task/bin/ogrinfo \
    /var/task/bin/ogr2ogr \
    /var/task/bin/proj \
    /var/task/bin/projinfo \
    /gdal/bin/

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

cd /gdal/ && zip --symlinks -ruq lambda-gdal.zip ./
