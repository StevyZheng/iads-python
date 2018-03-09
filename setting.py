# coding = utf-8
from tabulate import tabulate
import os


log_path = "/root/server_info"
server_ip = "192.168.0.150"
server_logpath = "~/iads_log"
check_list = ["lsscsi", "sas2ircu", "sas3ircu", "storcli", "smartctl", "zpool", "zfs", "lsblk"]

_header = [
	"Command",
	"Help text"
]
_data = []

iads_help_list = (
	["iads help", "Show this help menu."],
	["iads bios show info", "Show BIOS all info."],
	["iads bios show ver", "Show BIOS date version."],
	["iads bios show date", "Show BIOS date date."],
	["iads mem show model", "Show memory model."],
	["iads cpu show info", "Show CPU info."],
	["iads phy show err", "Show phys which have error."],
	["iads disk show smarterr", "Show disks which have errors."],
	["iads monitor gpu", "Monitor the temperature of GPUs and adjust the speed of the fan."],
	["iads monitor log", "Monitor the logs and save lsiutils."],
	["iads logging all", "Logging all the logs."],
	["iads logging print-err", "Print err logs."],
	["iads logging upload", "Upload the log to server, only used in product line."],
	["iads run linpack <minutes> \niads run paoyali <minutes>",
		"Run python linpack cpu and memory stress program,\nno param <minutes> means that always running. o_o"],
	["iads run reboot <sec>", "Run the reboot interval <sec>."],
	["iads run reboot clean", "Clean all the reboot log."],
	["iads run reboot rm", "Remove all reboot files."],
	["-iads zfs create-pool", "Create zpool named rpool"],
)
for line in iads_help_list:
	_data.append(line)

help_str = ("iads 1.0.0\n"
			"iads require dmidecode, smartctl, lsscsi, lsblk, sas3ircu, sas2ircu, ipmicfg, pkill.\n"
			"Please makesure these tools are installed.\n\n"
			"help menu list:")


def str_help_list():
	return "%s%s%s" % (help_str, os.linesep, tabulate(_data, _header, tablefmt="fancy_grid", stralign="left", numalign="left"))

