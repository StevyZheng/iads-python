# coding = utf-8
import os
import math
import threading
import time
from linux import bin_exists
from os.path import join as pjoin
from numpy import matrix, linalg, random, amax, asscalar
from linux import exe_shell, search_regex_one_line_string_column, search_regex_strings_column


def show_cpu_model():
	pass


def show_cpu_info():
	if not bin_exists("dmidecode"):
		print("dmidecode is not exists, please install dmidecode.")
		return
	# dmi_info_t = IadsLocalCmdExecuter().run_one_shell_cmd("dmidecode --type processor")
	dmi_info = exe_shell("dmidecode --type processor")
	version = search_regex_strings_column(dmi_info, ".*Version:.*", ":", 1)
	cpu_model = version[0]
	cpu_num = len(version)
	core = search_regex_one_line_string_column(dmi_info, ".*Core Count:.*", ":", 1)
	thread_t = search_regex_one_line_string_column(dmi_info, ".*Thread Count:.*", ":", 1)
	print("cpu model: %s\ncpu num: %s\ncore per cpu: %s\nthread per cpu: %s" % (cpu_model, cpu_num, core, thread_t))


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
