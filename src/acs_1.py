import urllib.request
import utils.logger as log
import commandLine.manager as cmd
import ec2.manager as ec2
import s3.manager as s3
import utils.openBrowser as browser

userData = """#!/bin/bash
yum update -y
yum install httpd -y
systemctl enable httpd
systemctl start httpd
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
echo '<html>' > index.html
echo 'Private IP address: ' >> index.html
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-
metadata-token-ttl-seconds: 21600"`
curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-
data/local-ipv4 >> index.html
cp index.html /var/www/html/index.html
"""

userDatabase = """#!/bin/bash
sudo yum update -y

echo '[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-7.0.asc' > /etc/yum.repos.d/mongodb-org-7.0.repo

yum install -y mongodb-org
sleep 30

systemctl enable mongod
systemctl start mongod

sleep 30

TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PUBLIC_DNS_NAME=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-hostname)
sed -i "s/bindIp: 127.0.0.1/bindIp: $PUBLIC_DNS_NAME/" /etc/mongod.conf
systemctl restart mongod
"""

website_configuration = {
    "IndexDocument": {"Suffix": "index.html"},
    "ErrorDocument": {"Key": "error.html"},
}

logger = log.setup_logger(name="APP")
def launch_monitoring_instance(filePath,ip):
        logger.info("Launching Monitoring EC2 Instance...")
        cmd.upload_file(
            key='data/demo.pem',
            ipAddress=ip,
            file="data/monitoring.sh"
        )
        cmd.run_command(
            key="data/demo.pem",
            ipAddress=ip,
            command='cd ~/script & chmod +x monitoring.sh && ./monitoring.sh'
        )

def launch_ec2_instance_DataBase():
    try:
        logger.info("Launching Database EC2 Instance...")
        ip,dns =ec2.launch_ec2_instance(
            instanceName="Ec2_Database(ACS)",
            keyName="demo",
            secuirtyGroupId="sg-032fa0004dc0327c2",
            userData=userDatabase,
        )
        browser.wait_for_url(f"http://{dns}:27017", 120, 60)
        launch_monitoring_instance(ip)
    except Exception as e:
        logger.error(f"Failed to launch EC2 instance: {e}")

def launch_ec2_instance():
    try:
        logger.info("Launching Metadata EC2 Instance...")
        ip,dns=ec2.launch_ec2_instance(
            instanceName="Ec2_Metadata(ACS)",
            keyName="demo",
            secuirtyGroupId="sg-032fa0004dc0327c2",
            userData=userData,
        )
        browser.open_browser("Metadata Website", f"http://{ip}")
        launch_monitoring_instance('data/monitoring.sh',ip)
    except Exception as e:
        logger.error(f"Failed to launch EC2 instance: {e}")


def launch_S3_bucket():
    bucketName=s3.create_s3_bucket("sConroy")
    urllib.request.urlretrieve('https://setuacsresources.s3-eu-west-1.amazonaws.com/image.jpeg', 'data/image.jpeg')
    s3.upload_file_to_bucket(bucketName, "data/image.jpeg", "image/jpeg")
    s3.upload_file_to_bucket(bucketName, "data/index.html", "text/html")
    s3.add_policy(bucketName)
    s3.website_configuration(bucketName, website_configuration)
    browser.open_browser("S3 Website", f"http://{bucketName}.s3-website-us-east-1.amazonaws.com")

def main():
    logger = log.setup_logger(name="acs_main")
    logger.info("Starting ACS Project")
    # launch_ec2_instance()
    launch_ec2_instance_DataBase()
    # launch_S3_bucket()
    
    
    


if __name__ == "__main__":
    main()
    