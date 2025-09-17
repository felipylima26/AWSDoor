import argparse
import boto3
from botocore.exceptions import ClientError
from .DoorModule import DoorModule

class AccessKey(DoorModule):
    class Meta:
        name = 'AWS Access Key'
        help = 'Add an access key to the given account'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-u',
            '--user',
            help='The user to add the access key to',
            required=True
        )
        args, _ = parser.parse_known_args(argv)
        self.user = args.user

    def run(self):
        iam_client = boto3.client('iam')
        try:
            response = iam_client.create_access_key(UserName=self.user)
            access_key = response['AccessKey']
            print(f'[+] Access key created for user: {self.user}')
            print(f'[+] Access key ID: {access_key["AccessKeyId"]}')
            print(f'[+] Access key Secret: {access_key["SecretAccessKey"]}')
        except ClientError as e:
            print(f"[x] Failed to create the access key: {e}")