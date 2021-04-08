#! bin/sh

# Build a wget Lambda Layer: Built on Amazon Linux
# docker run -ti --volume $(pwd)/utils:/utils amazonlinux --volume $(pwd)/layers/:/layers/ bash -c './layers/build_utils.sh'
    
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

cp /usr/bin/wget /utils/bin/ 

cd /utils/ &&\
    zip --symlinks -ruq lambda-deploy.zip ./