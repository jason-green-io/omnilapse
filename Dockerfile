FROM   ubuntu:18.04

ENV    DEBIAN_FRONTEND noninteractive

MAINTAINER Jason Green <jason@green.io>


RUN    apt-get --yes update; \
       apt-get --yes install sshfs openjdk-8-jre git wget imagemagick software-properties-common tmux man python python-pip python-dev vim htop ffmpeg curl

#RUN    pip install nbt2yaml watchdog slacker requests python-daemon twisted pyyaml websocket-client slackclient matplotlib

# RUN    apt-add-repository --yes ppa:webupd8team/java; \
#        apt-get --yes update

# RUN    echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections  && \
#        echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections  && \
#        apt-get --yes install oracle-java8-installer; \
#        apt-get clean

RUN    git clone https://github.com/google/spatial-media.git
       
COPY   . /spin_o_lapse

RUN    cd /spin_o_lapse; \
       curl -O http://chunkyupdate.llbit.se/ChunkyLauncher.jar; \
       java -jar ChunkyLauncher.jar --update; \
       java -jar ChunkyLauncher.jar -download-mc 1.10

CMD   tmux

