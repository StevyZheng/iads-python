# coding = utf-8
import os
from linux import bin_exists
from linux import exe_shell, search_regex_one_line_string_column


def show_mem_model():
	if not bin_exists("dmidecode"):
		print("dmidecode is not exists, please install dmidecode.")
		return
	dmi_info = exe_shell("dmidecode --type memory")
	print(search_regex_one_line_string_column(dmi_info, ".*Part Number:.*", ":", 1))