#! bin/sh

# Build a PSQL Client Lambda Layer: Built on Amazon Linux
# docker run -ti --volume $(pwd)/pgclient:/pgclient amazonlinux bash -c './layers/build_psql.sh'

sudo amazon-linux-extras install postgresql10

mkdir -p /pgclient/bin /pgclient/lib  &&\
    cp /usr/bin/psql /pgclient/bin/

ldd /usr/bin/psql |\
    grep "=> /" |\
    awk '{print $3}' |\
    xargs -I '{}' cp -v '{}' /pgclient/lib/

strip /pgclient/lib/* || true

cd /pgclient/ &&\
    zip --symlinks -ruq lambda-psql.zip ./

