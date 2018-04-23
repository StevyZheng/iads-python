# coding = utf-8
import time
from linux.sysinfo import Bmc


def gpu_temp_monitor():
	while True:
		Bmc.monitor_gpu_temp()
		time.sleep(4)


def matrix_mul_gpu():
	pass

