# Oracle Linux

FROM oraclelinux:8.4
MAINTAINER ZakFein (zak@zergling.ru)

WORKDIR "/root/work"
VOLUME "/etc/supervisord.d/"
VOLUME "/var/log/supervisor/"

RUN dnf -y install oracle-epel-release-el8

RUN dnf -y install nano wget cronie gettext rsyslog rsync supervisor 

RUN dnf -y install python39 python39-pip
RUN update-alternatives --set python3 /usr/bin/python3.9
RUN update-alternatives --set python /usr/bin/python3.9
RUN pip3 install requests
RUN python3 --version && pip3 --version

RUN dnf -y install libpq-devel gcc python39-devel  
RUN pip3 install setuptools wheel
RUN pip3 install asana pandas sqlalchemy psycopg2 datetime awscli boto3

RUN dnf -y install net-tools tar zip curl htop telnet screen

RUN echo "LANG=en_US.UTF-8" >> /etc/environment \
    echo "LC_ALL='en_US.UTF-8'" >> /etc/environment

ENV WORK_USER worker
RUN adduser --shell /bin/bash -g users $WORK_USER
RUN groupadd supervisor
RUN gpasswd -a $WORK_USER supervisor

#COPY supervisord.conf /etc/supervisor/supervisord.conf
RUN sed -i '/imklog/s/^/#/' /etc/rsyslog.conf

COPY entrypoint.sh /root/entrypoint.sh
RUN chmod 755 /root/entrypoint.sh

ENTRYPOINT ["/root/entrypoint.sh"]

CMD [""]