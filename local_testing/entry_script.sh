#!/bin/sh
echo "Running Emulator"
exec /aws-lambda/aws-lambda-rie /var/lang/bin/python aws-lambda-ric
