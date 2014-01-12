#!/usr/bin/env python
#
# Author: vishnu.srkmr@gmail.com
# Purpose: Connect to the load test servers and fetch the load test output file

import argparse,logging,paramiko
import boto

SSH_USER_NAME = 'ec2-user'
SSH_KEY_FILE = '/Users/vishnus/.ssh/vishnus_test_key_1.pem'
LOG_FILE = "/home/ec2-user/load_test.log"

#Enable logging
log_file = "/Users/vishnus/Documents/Projects/Flux7Labs/src/fetch_results.log"
logging.basicConfig(filename=log_file,level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%a, %d %b %Y %H:%M:%S',)


#Check if necessary env variables are set for boto connection
def check_env():
    env = os.environ
    if ('AWS_ACCESS_KEY_ID' not in env or 'AWS_SECRET_ACCESS_KEY' not in env):
        raise Exception("Environment must have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY set.")

def fetch_instances_by_tag(TAG):
    conn = boto.connect_ec2()
    reservations = conn.get_all_instances()
    instances = [ i for r in reservations for i in r.instances ]
    instance_list = []
    
    for i in instances:
        try:
            if i.tags['Name'] == TAG:
                instance_list.append(i.dns_name)
        except:
            logging.info("Skipping, no tag added for instance %s" % i.id)
    
    return instance_list

parser = argparse.ArgumentParser()
parser.add_argument("tag",help="Instance Tag")
args = parser.parse_args()

instance_list = fetch_instances_by_tag(args.tag)

#Download load test log from instances

for host in instance_list:
    LOCAL_LOG_FILE = host+"_load_test.log"
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh_client.connect(host,username=SSH_USER_NAME,key_filename=SSH_KEY_FILE)
        ftp = ssh_client.open_sftp()
        ftp.get(LOG_FILE,LOCAL_LOG_FILE)
        ftp.close()
    except:
        logging.error("Failed to connect to %s" % host)

