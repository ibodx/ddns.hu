FROM registry.access.redhat.com/ubi8/ubi

RUN yum -y update && \
    yum -y install python3-pip git && \
    yum clean all

RUN mkdir -p /root/ddnsApp
WORKDIR /root/ddnsApp

COPY requirements.txt /root/ddnsApp/
RUN pip3 install --no-cache-dir -r requirements.txt

RUN firewall-cmd --zone=public --permanent --add-service=dns --add-service=http --add-service=https --add-icmp-block-inversion && \
    firewall-cmd --zone=public --permanent --add-port=27017/tcp --add-port=27018/tcp && \
    firewall-cmd --reload

RUN git clone https://github.com/ibodx/ddns.hu.git .

ENV mongoDB_url=<your_mongoDB_url>
ENV db=<your_db_name>
ENV dns_col=<your_dns_collection_name>
ENV app.secret_key=<your_secret_key>
ENV dnsserver_ip=<your_dnsserver_ip>
ENV zone=<your_zone_name>

EXPOSE 443

RUN touch /etc/systemd/system/ddnsApp.service && \
    echo "[Unit]
Description=Flask Application
After=network.target

[Service]
User=root
WorkingDirectory=/root/ddnsApp
ExecStart=/usr/bin/python3 /root/ddnsApp/app.py
Restart=always

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/ddnsApp.service

RUN systemctl daemon-reload && \
    systemctl enable ddnsApp.service && \
    systemctl start ddnsApp.service


