#! bin/sh

# Build a wget Lambda Layer: Built on Amazon Linux    
yum -y update &&\
    yum install -y \
        wget \
        zip \
        binutils
        
# WGET
mkdir -p /utils/lib &&\
    ldd /usr/bin/wget |\
        grep "=> /" |\
        awk '{print $3}' |\
        xargs -I '{}' cp -v '{}' /utils/lib

strip /utils/lib/* || true

mkdir -p /utils/bin/ &&\
    cp /usr/bin/wget /utils/bin/ 

cd /utils/ &&\
    zip --symlinks -ruq lambda-deploy.zip ./