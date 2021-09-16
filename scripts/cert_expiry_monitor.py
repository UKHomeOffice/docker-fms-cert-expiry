import json
import logging
import urllib.parse
import datetime
import sys
import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

CONFIG = Config(
    retries=dict(
        max_attempts=20
    )
)

logging.basicConfig(filename='/home/ssl_expire_script/expiry.log', level=logging.INFO)

get_expiry = os.getenv('GET_EXPIRY_COMMAND')
expiry_file = "/home/ssl_expire_script/cert_expiry.txt"
now = datetime.datetime.today()
now = now.strftime("%Y-%m-%d %H:%M:%S")
bucket = os.getenv('BUCKET')
home = os.getenv('HOME')
slack_notification_webhook = os.getenv('SLACK_NOTIFICATION_WEBHOOK')

def error_handler(lineno, error, fail=True):

    try:
        logging.error('The following error has occurred on line: %s', lineno)
        logging.error(str(error))

        send_message_to_slack(
            'An Error has occured with the get certificate expiry script!')
        if fail:
            sys.exit(1)

    except Exception as err:
        error_handler(sys.exc_info()[2].tb_lineno, err)
        logging.error(
            'The following error has occurred on line: %s',
            sys.exc_info()[2].tb_lineno)
        logging.error(str(err))
        sys.exit(1)


def send_message_to_slack(text):
    """
    Formats the text provides and posts to a specific Slack web app's URL
    Args:
        text : the message to be displayed on the Slack channel
    Returns:
        Slack FMS repsonse
    """

    try:
        post = {
            "text": ":fire: :sad_parrot: *SSL Certificate Expiration Status for FMS:* :sad_parrot: :fire:",
            "attachments": [
                {
                    "text": "{0}".format(text),
                    "color": "#B22222",
                    "attachment_type": "default",
                    "fields": [
                        {
                            "title": "Priority",
                            "value": "High",
                            "short": "false"
                        }
                    ],
                    "footer": "AWS FMS",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
                }
            ]
        }

        ssm_param_name = slack_notification_webhook
        ssm = boto3.client('ssm', config=CONFIG, region_name='eu-west-2')
        try:
            response = ssm.get_parameter(
                Name=ssm_param_name, WithDecryption=True)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                LOGGER.info(
                    'Slack SSM parameter %s not found. No notification sent', ssm_param_name)
                return
            else:
                logging.error(
                    "Unexpected error when attempting to get Slack webhook URL: %s", e)
                return
        if 'Value' in response['Parameter']:
            url = response['Parameter']['Value']

            json_data = json.dumps(post)
            req = urllib.request.Request(
                url,
                data=json_data.encode('ascii'),
                headers={'Content-Type': 'application/json'})
            LOGGER.info('Sending notification to Slack')
            response = urllib.request.urlopen(req)

        else:
            LOGGER.info(
                'Value for Slack SSM parameter %s not found. No notification sent', ssm_param_name)
            return

    except Exception as err:
        logging.error(
            'The following error has occurred on line: %s',
            sys.exc_info()[2].tb_lineno)
        logging.error(str(err))

def check_expiry():

    try:
        os.system(f"aws s3 cp s3://{bucket}/fms-certificate.pem {home}")
        os.system(f"{get_expiry} > {expiry_file}")

        #strip unwanted text from get_expiry to get enddate <class 'str'>
        f = open(expiry_file, "r")
        for date in f:
            date = date[9:]
            # remove whitespace after enddate
            enddate_str = date.strip()

        #convert enddate_str to datetime
        enddate_obj = datetime.datetime.strptime(enddate_str, "%b %d %H:%M:%S %Y %Z")
        logging.info(f"Certificate expiry datetime is: {enddate_obj}")

        #convert now_str to datetime
        now_obj = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        logging.info(f"Current datetime is: {now_obj}")

        #Get the length of period between now and enddate
        renewal_length = enddate_obj - now_obj
        logging.info(f"Renewal length: {renewal_length}")


        #if we have 0 days to renew send message to slack
        if renewal_length <= datetime.timedelta(days=0):
           logging.info(f"Your SSL Certificates for fms has expired by {renewal_length} days")
           os.system(f"aws s3 cp expiry.log s3://{bucket}/")
           logging.info(f"Uploaded expiry.log to: {bucket}")
           send_message_to_slack(f"Your SSL Certificates for fms has expired by {renewal_length} days")

        #if we have between 1 and 30 days left to renew send message to slack
        if  renewal_length <= datetime.timedelta(days=30) and renewal_length > datetime.timedelta(days=0):
            logging.info(f"Your SSL Certificates for fms is about to expire in {renewal_length} days")
            os.system(f"aws s3 cp expiry.log s3://{bucket}/")
            logging.info(f"Uploaded expiry.log to: {bucket}")
            send_message_to_slack(f"Your SSL Certificates for fms is about to expire in {renewal_length} days")

        #if we have more than 30 days left to renew then we are good
        if  renewal_length > datetime.timedelta(days=30):
            logging.info(f"Certificates are Valid: {renewal_length} Remaining before expiry approaches...")
            os.system(f"aws s3 cp expiry.log s3://{bucket}/")
            logging.info(f"Uploaded expiry.log to: {bucket}")
            send_message_to_slack(f"Certificates are Valid: {renewal_length} Remaining before expiry approaches...")

    except Exception as err:
        error_handler(sys.exc_info()[2].tb_lineno, err)

check_expiry()
