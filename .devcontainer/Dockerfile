# Author: mail@piotrkowalski.info
# Originally written for Fedora-Dockerfiles by
#   scollier <scollier@redhat.com>

FROM centos:centos7
#FROM registry.access.redhat.com/ubi8

RUN yum --disableplugin=subscription-manager -y update; yum clean all
RUN yum --disableplugin=subscription-manager -y install openssh-server openssh-clients passwd python3; yum clean all
RUN python3 -m pip install --upgrade pip
#RUN python3 -m pip install --upgrade
#    paramiko
#ADD ./start.sh /start.sh
RUN mkdir /var/run/sshd

RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N '' 

#RUN chmod 755 /start.sh
# EXPOSE 22
#RUN ./start.sh
#ENTRYPOINT ["/usr/bin/bash"]

CMD /usr/bin/bash
