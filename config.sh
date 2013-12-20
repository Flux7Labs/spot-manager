# NAME_TAG : AS Groups will be created as spot-NAME_TAG and ondemand-NAME_TAG
# SPOT_PRICE : Max bid for spot instances
# AMI : AMI used while launching instances
# INSTANCE_TYPE :
# SECURITY_GROUP :
# SECURITY_KEY :
# AZ : Availability Zones

export NAME_TAG=12202013-test
export SPOT_PRICE=0.01
export AMI=ami-85a08cec
export INSTANCE_TYPE=t1.micro
export AZ=us-east-1a
export SECURITY_KEY=vishnus-test-key
export SECURITY_GROUP=spot-monitor-test
export SNS_ARN=arn:aws:sns:us-east-1:547078464708:spot-group-scaling-alerts
