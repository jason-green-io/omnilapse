#!/bin/bash


docker run -h spin-o-lapse -it --security-opt apparmor:unconfined --cap-add SYS_ADMIN --device /dev/fuse -v /home/spin-o-lapse:/data --name spin-o-lapse spin-o-lapse:latest
