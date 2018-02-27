#!/usr/bin/env python
# coding=utf-8
import os
import time
import subprocess
import threading
from os.path import join as pjoin

log_path = "/var/log/monitor"
gpu_log = pjoin(log_path, "gpu_temp.log")
dmesg_log = pjoin(log_path, "dmesg.log")
sys_log = pjoin(log_path, "sys.log")
gpu_temp_cmd = "nvidia-smi|grep -P '.+\d+C.+W.+W.+'"
dmesg_cmd = "dmesg"
sys_cmd = "top -b -n 1"


class MonitorException(Exception):
	pass


def execute(cmd):
	pipe = subprocess.PIPE
	exec_context = subprocess.Popen(cmd, shell=True, stdin=pipe, stdout=pipe, stderr=pipe)
	out, err = exec_context.communicate()
	return out, err


def write_log(filename, string, is_append):
	if is_append:
		flag = 'a'
	else:
		flag = 'w'
	with open(filename, flag) as fp:
		fp.write("%s%s%s%s%s%s" % (
			time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
			os.linesep,
			string,
			os.linesep,
			"=" * 60,
			os.linesep))

monitor_dict = {
	"gpu": True,
	"dmesg": True,
	"sys": True
}


def init():
	if not os.path.exists(log_path):
		os.makedirs(log_path)
	if execute("nvidia-smi")[0] == '':
		monitor_dict["gpu"] = False


def monitor_gpu_temp():
	while True:
		out, err = execute(gpu_temp_cmd)
		if err == '':
			write_log(gpu_log, out, True)
		time.sleep(20)


def monitor_dmesg():
	while True:
		out, err = execute(dmesg_cmd)
		if err == '':
			write_log(dmesg_log, out, False)
		time.sleep(0.1)


def monitor_sys():
	while True:
		out, err = execute(sys_cmd)
		if err == '':
			write_log(sys_log, out, True)
		time.sleep(10)


def run():
	threads = {}
	if monitor_dict["gpu"]:
		threads["gpu"] = threading.Thread(target=monitor_gpu_temp)
	if monitor_dict["dmesg"]:
		threads["dmesg"] = threading.Thread(target=monitor_dmesg)
	if monitor_dict["sys"]:
		threads["sys"] = threading.Thread(target=monitor_sys)
	for key in threads:
		threads[key].start()
	for key in threads:
		threads[key].join()


if __name__ == "__main__":
	init()
	run()

