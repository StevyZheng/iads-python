# coding = utf-8
import os
import string
from linux.storage.phy import Phy
from linux import exe_shell
from tabulate import tabulate


def show_err_phy():
	if not os.path.exists("/sys/class/sas_phy"):
		print("System has no sas_phys.")
		return
	_header = [
		"phy_name",
		"sas_address",
		"invalid_dword",
		"loss_of_dword_sync",
		"phy_reset_problem",
		"running_disparity",
	]
	_data = []
	err_phy_arr = Phy.scan_err_phys()
	for i in err_phy_arr:
		_data.append([
			i.phy_name,
			i.sas_address,
			i.invalid_dword_count,
			i.loss_of_dword_sync_count,
			i.phy_reset_problem_count,
			i.running_disparity_error_count
		])
	print(tabulate(_data, _header, tablefmt="fancy_grid", stralign="center", numalign="center"))


def write_a(file_t, str_t):
	with open(file_t, "a") as fp:
		fp.write(str_t)


def get_lsi_phy_list(phy_list):
	lsi_phy_list = []
	for i in phy_list:
		if "5000ccab" not in i.sas_address:
			lsi_phy_list.append(i)
	return lsi_phy_list


def log_monitor():
	start_log_path = "/var/log/start-iads-monitor-log.log"
	log_path = "/var/log/iads-monitor-log.log"
	start_time_t = exe_shell("date")

	start_lsi_str = exe_shell("lsiutil.x86_64_171  -p  1  -a  64,1,,debuginfo,exit,0")
	start_hba_str = exe_shell("lsiutil.x86_64_171  -p  1  -a  65,,'pl dbg',exit,0")
	start_dmesg_str = exe_shell("dmesg|grep -iP '((i/o error)|(sector [0-9]+))'")
	start_messages_str = exe_shell("cat /var/log/messages|grep -iP '((i/o error)|(sector [0-9]+))'")
	start_str = "\ntime:\n%s\ndmesg:\n%s\n\nmessage:\n%s\n\nlsiutils debuginfo:\n%s\n\nlsiutils_pl dbg:\n%s\n\n" % (start_time_t, start_dmesg_str, start_messages_str, start_lsi_str, start_hba_str)
	with open(start_log_path, "a") as fp:
		fp.write(start_str)
	print("Start_log is OK. path: /var/log/start-iads-monitor-log.log \n")

	i_times = 0
	phy_t_list = get_lsi_phy_list(Phy.scan_phys_attr())
	collect = False
	while True:
		g_lsi_str = exe_shell("lsiutil.x86_64_171  -p  1  -a  64,1,,debuginfo,exit,0")
		g_hba_str = exe_shell("lsiutil.x86_64_171  -p  1  -a  65,,'pl dbg',exit,0")
		dmesg_str = exe_shell("dmesg|grep -iP '((i/o error)|(sector [0-9]+))'")
		phy_list = get_lsi_phy_list(Phy.scan_phys_attr())
		if len(phy_t_list) != len(phy_list):
			collect = True
		else:
			for i in range(0, len(phy_list)):
				if phy_list[i].invalid_dword_count != phy_t_list[i].invalid_dword_count or phy_list[
					i].loss_of_dword_sync_count != phy_t_list[i].loss_of_dword_sync_count:
					collect = True
				if phy_list[i].phy_reset_problem_count != phy_t_list[i].phy_reset_problem_count or phy_list[
					i].running_disparity_error_count != phy_t_list[i].running_disparity_error_count:
					collect = True
		if not collect:
			continue
		print("Phy err increased.Start collect logs to /var/log/iads-monitor-log.log......")
		phy_t_list = phy_list

		messages_str = exe_shell("cat /var/log/messages|grep -iP '((i/o error)|(sector [0-9]+))'")
		i_times += 1
		time_t = exe_shell("date")
		lsi_str = exe_shell("lsiutil.x86_64_171  -p  1  -a  64,1,,debuginfo,exit,0")
		hba_str = exe_shell("lsiutil.x86_64_171  -p  1  -a  65,,'pl dbg',exit,0")
		tmp_str = "\n%s\ndmesg:\n%s\nmessages:\n%s\nbefore_lsi_str:\n%s\nafter_lsi_str:\n%s\nbefore_hba_lig:\n%s\nafter_hba_log:\n%s\n" % (
		time_t, dmesg_str, messages_str, g_lsi_str, lsi_str, g_hba_str, hba_str)
		with open(log_path, "a") as fp:
			fp.write(tmp_str)
			fp.writelines("\n\n\nsmart info:\n")
		for case in ("", "a", "b", ):
			for i in string.lowercase:
				write_a(log_path, "\nsd%s%s\n" % (case, i))
				exe_shell("smartctl -x /dev/sd%s%s >> /var/log/iads-monitor-log.log" % (case, i))
		exe_shell("lsigetlunix.sh")
		break
