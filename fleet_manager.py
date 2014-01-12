#!/usr/bin/env python

# Author: vishnu.srkmr@gmail.com
# Purpose: Launch reuired number of EC2 instances and initiate load test

from boto.ec2.connection import EC2Connection
from boto.exception import AWSConnectionError
import argparse,os,logging,time
import paramiko


IMAGE = 'ami-35ffce5c'
KEY_NAME = 'vishnus_test_key_1'
INSTANCE_TYPE = 'm1.medium'
SECURITY_GROUP = ['load_test_group']
SSH_KEY_FILE = '/Users/vishnus/.ssh/vishnus_test_key_1.pem'
SSH_USER_NAME = 'ec2-user'
SSH_EXEC_COMMAND = 'nohup sh /home/ec2-user/load_gen.sh 20 2 sanketalgotest-46422949.us-east-1.elb.amazonaws.com'

#Enable logging
log_file = "/Users/vishnus/Documents/Projects/Flux7Labs/src/fleet_manager.log"
logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',)

#Check if necessary env variables are set for boto connection
def check_env():
    env = os.environ
    if ('AWS_ACCESS_KEY_ID' not in env or 'AWS_SECRET_ACCESS_KEY' not in env):
        raise Exception("Environment must have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY set.")
    
def launch_ec2_instance():
    try:
        conn = EC2Connection()
    except AWSConnectionError as aws_conn_err:
        logging.error("Error connecting to EC2, exception: %r" % aws_conn_err)
    try:
        reservation = conn.run_instances(IMAGE,instance_type=INSTANCE_TYPE, key_name=KEY_NAME,security_groups=SECURITY_GROUP)
    except Exception, e:
        logging.error("Error creating instance, exception: %r" % e)
    instance = reservation.instances[0]
    time.sleep(10)
    while not instance.update() == 'running':
        time.sleep(5)
    time.sleep(10)
    instance.add_tag("Name","load_test")
    logging.info("Started instance %s" % instance.id)
    return instance.dns_name

parser = argparse.ArgumentParser()
parser.add_argument("n",help="Number of instances")
args = parser.parse_args()

count = 0
instance_list = []
while (count < int(args.n)):
    instance_list.append(launch_ec2_instance())
    count += 1

#Connect to the instances and launch the load test script

for host in instance_list:
    logging.info("Connecting to %s" % host)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(host,username=SSH_USER_NAME,key_filename=SSH_KEY_FILE)
        stdin, stdout, stderr = ssh_client.exec_command(SSH_EXEC_COMMAND)
        ssh_client.close()
    except Exception, e:
        logging.error("Error connecting to %s, exception: %r" % (host,e))
    

