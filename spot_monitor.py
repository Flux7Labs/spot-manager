#!/usr/bin/env python
#
# Author : Vishnu <vishnu.srkmr@gmail.com>
# Purpose:

import logging,time,argparse,os,json,re
import boto

#PRESETS
MAX_RETRIES = 5

#Enable logging
log_file = "/tmp/vyscale.log"
logging.basicConfig(filename=log_file, level=logging.ERROR)


#Function defenitions
def connect_to_queue(queue):
    """ Check if necessary env variables for SQS connection is set and initiate the connect function """
    env =os.environ
    if ('AWS_ACCESS_KEY_ID' not in env or 'AWS_SECRET_ACCESS_KEY' not in env):
        raise Exception("Environment must have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY set.")
    process_queue(queue)


def process_queue(queue):
    """ Connect to the given queue and listen for messages """
    retries = 0
    delay = 5
    
    conn = boto.connect_sqs()
    q = conn.get_queue(queue)
    
    while True:
        try:
            rs = q.get_messages()
            for msg in rs:
                if process_message(msg):
                    q.delete_message(msg)
                
            #Wait for 10 seconds before checking the queue again    
            time.sleep(10)
            
            #Reset retries and delay
            retries = 0
            delay = 5
        except SQSError as sqse:
            retries += 1
            logging.info("Error in SQS, attempting to retry: attempt: %d, excemption: %r" % (retries,sqse))
            if retries >= MAX_RETRIES:
                log.error("Max retries hit, giving up")
                raise sqse
            else:
                #Wait fro delay seconds and increase delay by 1.2
                time.sleep(delay)
                delay *= 1.2

def process_message(msg):
    """ Process the SQS message from the queue """
    try:
        m = json.loads(msg.get_body())
    except ValueError:
        #Message not in json format, ignore it.
        logging.errror("Could not decode: %s" % (msg.get_body()))
        return True
    
    #Check if the mesage is a notification from AWS
    msg_type = m['Type']
    if msg_type == 'Notification':
        payload = json.loads(m['Message'])
        spot_group = payload.get('AutoscalingGroupName', '')
        cause = payload.get('Cause')
        event = payload.get('Event')
        
        #Check if autoscaling group for which the alert came is a spot group
        if not is_spot_group(spot_group):
            log.info("Received AWS notification for non-spot group %s, ignoring." % spot_group )
            return True
        
        #NEED TO TEST THIS PART WITH JSON MESSAGE FORMAT
        
        if not re.search(r'was taken out of service in response to a (system|user) health-check.', cause):
            logging.info("Received notification for spot group %s is not due to health-check termination, ignoring." % spot_group)
            return True
        
        if event == 'autoscaling:EC2_INSTANCE_TERMINATE':
            adjust_demand_group(spot_group, 1)
        else:
            log.info("Ignoring notification: %s", payload)

def is_spot_group(group_name):
    """ Returns true if the group's name contains spot """
    return '-spot-' in group_name



# Call the connect function and pass the queue name

parser = argparse.ArgumentParser()
parser.add_argument("queue", help="SQS queue name")
args = parser.parse_args()

connect_to_queue(args.queue)