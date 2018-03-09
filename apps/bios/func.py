# coding = utf-8
import os
from linux import exe_shell, search_regex_one_line_string_column


def show_bios_info():
	"""show server's bios info."""
	if not os.path.exists("/usr/sbin/dmidecode"):
		print("dmidecode is not exists, please install dmidecode.")
		return
	dmi_info = exe_shell("dmidecode --type bios")
	print(dmi_info)


def show_bios_date():
	if not os.path.exists("/usr/sbin/dmidecode"):
		print("dmidecode is not exists, please install dmidecode.")
		return
	dmi_info = exe_shell("dmidecode --type bios")
	print(search_regex_one_line_string_column(dmi_info, ".*Release Date:.*", ":", 1))


def show_bios_ver():
	if not os.path.exists("/usr/sbin/dmidecode"):
		print("dmidecode is not exists, please install dmidecode.")
		return
	dmi_info = exe_shell("dmidecode --type bios")
	print(search_regex_one_line_string_column(dmi_info, ".*Version:.*", ":", 1))