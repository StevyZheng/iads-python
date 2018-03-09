# coding = utf-8
from linux.storage.phy import Phy
from linux.storage.controller import Controller
from linux.storage.disk import Disk
from linux.sysinfo import *
from linux import *
from setting import *
import datetime


def list_dict(dict_a):
	if isinstance(dict_a, dict):
		for x in range(len(dict_a)):
			temp_key = dict_a.keys()[x]
			temp_value = dict_a[temp_key]
			if not isinstance(temp_value, dict):
				print("%s : %s" % (temp_key, temp_value))
			list_dict(temp_value)


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
