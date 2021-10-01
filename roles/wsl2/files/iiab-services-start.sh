#!/bin/bash -x
for p in uwsgi nginx kalite-serve kiwix-serve iiab-cmdsrv;do
    if [ $(systemctl is-active $p.service) != "active" ];then
	echo starting $p.service
	sudo systemctl restart $p.service
    else
	echo $p.service already started
    fi
done

