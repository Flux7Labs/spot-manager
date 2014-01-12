#!/usr/bin/env python
#
# Author : Vishnu <vishnu.srkmr@gmail.com>
# Purpose:

import logging,time,argparse,os,json,re
import boto
from boto.sqs.message import RawMessage
from boto.exception import SQSError

#PRESETS
MAX_RETRIES = 5

#Enable logging
log_file = "/Users/vishnus/Documents/Projects/Flux7Labs/src/vyscale.log"
logging.basicConfig(filename=log_file, level=logging.INFO)


#Function defenitions
def is_spot_group(group_name):
    """ Returns true if the group's name contains spot """
    return 'spot-' in group_name

def find_demand_scaling_group(spot_group):
    """ Find corresponding on-demand group for the given spot-group """
    #Connect to autoscale and fetch all group names
    autoscale = boto.connect_autoscale()
    as_groups = autoscale.get_all_groups()
    
    #Strip the identifier from the group name
    demand_group = re.sub(r'spot-', r'', spot_group)
    demand_group = re.sub(r'-\d+$', r'', demand_group)
    logging.debug("Given spot group %s, find demand group corresponding to %s" % (spot_group,demand_group))
    
    result = [ group for group in as_groups
              if demand_group in group.name and not is_spot_group(group.name) ]
    return sorted(result, key=lambda group: group.name).pop() if result else None

def connect_to_queue(queue):
    """ Check if necessary env variables for SQS connection is set and initiate the connect function """
    env = os.environ
    if ('AWS_ACCESS_KEY_ID' not in env or 'AWS_SECRET_ACCESS_KEY' not in env):
        raise Exception("Environment must have AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY set.")
    process_queue(queue)

def process_queue(queue):
    """ Connect to the given queue and listen for messages """
    retries = 0
    delay = 5
    
    conn = boto.connect_sqs()
    q = conn.create_queue(queue)
    q.set_message_class(RawMessage)
    
    while True:
        try:
            rs = q.get_messages()
            for msg in rs:
                if process_message(msg):
                    #logging.info("Deleting message after processing")
                    try:
                        q.delete_message(msg)
                    except:
                        logging.info("Failed to delete processed message from queue")
            
            #logging.info("Hit the loop again.")    
            #Wait for 10 seconds before checking the queue again    
            time.sleep(10)
            
            #Reset retries and delay
            retries = 0
            delay = 5
        except SQSError as sqse:
            retries += 1
            logging.info("Error in SQS, attempting to retry: attempt: %d, excemption: %r" % (retries,sqse))
            if retries > MAX_RETRIES:
                logging.error("Max retries hit, giving up")
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
        logging.error("Could not decode: %s" % (msg.get_body()))
        return True
    
    #Check if the mesage is a notification from AWS
    msg_type = m['Type']
    if msg_type == 'Notification':
        try:
            payload = json.loads(m['Message'])
        except ValueError:
            #Message body not in jason format
            logging.error("Could not decode: %s" % m['Message'])
            return True
        spot_group = payload.get('AutoScalingGroupName', '')
        cause = payload.get('Cause', '')
        event = payload.get('Event', '')
        
        #Check if autoscaling group for which the alert came is a spot group
        if not is_spot_group(spot_group):
            logging.info("Received AWS notification for non-spot group %s, ignoring." % spot_group )
            return True
        
        
        if not re.search(r'was taken out of service in response to a (system|user) health-check.', cause):
            logging.info("Received notification for spot group %s is not due to health-check termination, ignoring." % spot_group)
            return True
        
        if event == 'autoscaling:EC2_INSTANCE_TERMINATE':
            #Good to add a check here to compare the current spot price and bid value to make sure that the instance got
            #terminated due to low bid value
            adjust_demand_group(spot_group, 1)
        else:
            logging.info("Ignoring notification: %s", payload)
            return True
        
        #Place holder for function to reduce the desired capacity of on-demand group when a new instance gets launched in spot group.

def adjust_group(group, adjustment):
    """ Change the number of instances in the given group by the given adjustment """
    try:
        current_capacity = group.desired_capacity
        desired_capacity = current_capacity + adjustment
        if desired_capacity < group.min_size or desired_capacity > group.max_size:
            logging.info("Demand group count already at bound, adjust as group settings if necessary.")
            return True
        group.desired_capacity = desired_capacity
        group.min_size = desired_capacity
        group.update()
        logging.info("Adjusted instance count of ASG %s from %d to %d." % (group.name, current_capacity, desired_capacity))
        return True
    except Exception as e:
        logging.exception(e)

def adjust_demand_group(spot_group, adjustment):
    """ Get the group object and pass it along with adjustment to change the number of instances """
    try:
        demand_group = find_demand_scaling_group(spot_group)
        if demand_group:
            adjust_group(demand_group, adjustment)
        else:
            logging.error("No demand group found similar to %s" % spot_group)
            return True
    except Exception as e:
        logging.exception(e)


# Call the connect function and pass the queue name
parser = argparse.ArgumentParser()
parser.add_argument("queue", help="SQS queue name")
args = parser.parse_args()

connect_to_queue(args.queue)