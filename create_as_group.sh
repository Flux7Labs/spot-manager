#!/bin/sh
#
# Author: Vishnu Sreekumar
# Purpose: Create spot instance and on-demand autoscale groups

#Import config file
CONFIG_FILE=$1

source $CONFIG_FILE

#Create launch configs
as-create-launch-config spot-lc-${NAME_TAG} --image_id ${AMI} --group ${SECURITY_GROUP} --instance-type ${INSTANCE_TYPE} --key ${SECURITY_KEY} --spot-price ${SPOT_PRICE}
as-create-launch-config ondemand-lc-${NAME_TAG} --image_id ${AMI} --group ${SECURITY_GROUP} --instance-type ${INSTANCE_TYPE} --key ${SECURITY_KEY}

#Create auto-scaling groups
as-create-auto-scaling-group spot-${NAME} --launch-configuration spot-lc-${NAME_TAG} --availability-zones ${AZ} --default-cooldown 600 --min-size 1 --max-size 2
as-create-auto-scaling-group ondemand-${NAME} --launch-configuration ondemand-lc-${NAME_TAG} --availability-zones ${AZ} --default-cooldown 600 --min-size 0 --max-size 2

#END