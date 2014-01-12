#!/bin/sh
#
# Author: Vishnu Sreekumar
# Purpose: Create spot instance and on-demand autoscale groups

#Import config file
CONFIG_FILE=$1

source $CONFIG_FILE

#Create launch configs
#as-create-launch-config spot-lc-${NAME_TAG} --image-id ${AMI} --group ${SECURITY_GROUP} --instance-type ${INSTANCE_TYPE} --key ${SECURITY_KEY} --spot-price ${SPOT_PRICE}
#as-create-launch-config ondemand-lc-${NAME_TAG} --image-id ${AMI} --group ${SECURITY_GROUP} --instance-type ${INSTANCE_TYPE} --key ${SECURITY_KEY}

#Create auto-scaling groups
as-create-auto-scaling-group spot-${NAME_TAG} --launch-configuration spot-lc-${NAME_TAG} --availability-zones ${AZ} --default-cooldown 600 --min-size 1 --desired-capacity 2 --max-size 3
as-create-auto-scaling-group ondemand-${NAME_TAG} --launch-configuration ondemand-lc-${NAME_TAG} --availability-zones ${AZ} --default-cooldown 600 --min-size 0 --desired-capacity 0 --max-size 2

#Define notification configuration
for group in spot ondemand
do
  as-put-notification-configuration ${group}-${NAME_TAG} -t "${SNS_ARN}" -n autoscaling:EC2_INSTANCE_LAUNCH, autoscaling:EC2_INSTANCE_TERMINATE
done

#END
