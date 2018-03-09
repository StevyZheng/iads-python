# coding = utf-8
from linux.storage.phy import Phy
from linux.storage.controller import Controller
from linux.storage.disk import Disk
from linux.sysinfo import *
from linux import *
from setting import *
import time
import datetime
from numpy import matrix, linalg, random, amax, asscalar
import math
import threading


def list_dict(dict_a):
	if isinstance(dict_a, dict):
		for x in range(len(dict_a)):
			temp_key = dict_a.keys()[x]
			temp_value = dict_a[temp_key]
			if not isinstance(temp_value, dict):
				print("%s : %s" % (temp_key, temp_value))
			list_dict(temp_value)


def gpu_monitor():
	while True:
		Bmc.monitor_gpu_temp()
		time.sleep(4)


def collect_err_log():
	err_sysinfo = SysInfo().analyze_dmesg()
	phys_err_dict = Phy.err_phys_to_dict()
	disk_err_dict = Disk.get_err_disk_dict()
	t_dict = {
		"get_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		"sys_err_log": err_sysinfo,
		"phys_err_log": phys_err_dict,
		"disk_err_log": disk_err_dict
	}
	return t_dict


def collect_all_log():
	log_dict = Log.get_all_log()
	phys_dict = Phy.phys_to_dict()
	disk_log = Controller.get_controllers_disks_all_dict()
	t_dict = {
		"get_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
		"sys_log": log_dict,
		"phys_log": phys_dict,
		"disk_log": disk_log
	}
	return t_dict


def write_all_log():
	t_dict = collect_all_log()
	if not os.path.exists(log_path):
		os.mkdir(log_path)
	json_path = os.path.join(log_path, "log.json")
	dict_to_json_file(t_dict, json_path)


def print_err_log():
	t_dict = collect_err_log()
	print(dict_to_json(t_dict))


def upload_logfile_to_server():
	json_path = os.path.join(log_path, "log.json")
	re = exe_shell("sshpass -p 000000 scp %s root@%s:%s" % (json_path, server_ip, server_logpath))
	if "" == re:
		print("Upload %s success." % json_path)
	else:
		print("Upload failed. Cannot connect to the server!")


def linpack_run():
	# (N*N*2*8.00+N*5)/1024/1024/1024=mem_size
	# a = malloc(n * n * sizeof(double));
	# a2 = malloc(n * n * sizeof(double));
	# b = malloc(n * sizeof(double));
	# b2 = malloc(n * sizeof(double));
	# x = malloc(n * sizeof(double));
	# r = malloc(n * sizeof(double));
	# ipvt = malloc(n * sizeof(int));
	tmp = int(exe_shell("free -g|grep Mem|awk '{print$7}'"))
	mem_size = int(tmp * 0.85)
	N = int((math.sqrt(25 + 64 * 1024 * 1024 * 1024 * mem_size) - 5) / 32)
	eps = 2.22e-16
	ops = (2.0 * N) * N * N / 3.0 + (2.0 * N) * N
	A = random.random_sample((N, N)) - 0.5
	B = A.sum(axis=1)
	A = matrix(A)
	B = matrix(B.reshape((N, 1)))
	na = amax(abs(A.A))
	t = time.time()

	while True:
		X = linalg.solve(A, B)
		t = time.time() - t
		R = A * X - B
		Rs = asscalar(max(abs(R.A)))
		nx = asscalar(max(abs(X)))
		print("Residual is ", Rs)
		print("Normalised residual is ", Rs / (N * na * nx * eps))
		print("Machine epsilon is ", eps)
		print("x[0]-1 is ", asscalar(X[0]) - 1)
		print("x[n-1]-1 is ", asscalar(X[N - 1]) - 1)


def run_linpack(r_t=-1):
	t2 = threading.Thread(target=linpack_run)
	t2.setDaemon(True)
	t2.start()
	r_t = int(r_t) * 60
	if r_t != -60:
		while r_t > 0:
			r_t -= 1
			time.sleep(1)
	else:
		t2.join()


def run_reboot(sec):
	reboot(sec)
	while True:
		user_in = raw_input("Reboot now ?  [y/n]")
		if "y" == user_in:
			exe_shell("reboot")
		elif "n" == user_in:
			break


def clean_reboot():
	clean_reboot_log()


def rm_reboot():
	rm_reboot_t()
