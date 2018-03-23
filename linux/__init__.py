# coding = utf-8
import traceback
import subprocess
import re
import os
import sys
import shutil
import stat
import json
from os.path import join as pjoin
from setting import *
from iadslib.iadsLocalCmdExecuter import IadsLocalCmdExecuter


def try_catch(f):
	def handle_problems(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception:
			exc_type, exc_instance, exc_traceback = sys.exc_info()
			formatted_traceback = ''.join(traceback.format_tb(exc_traceback))
			message = '\n{0}\n{1}:\n{2}'.format(
				formatted_traceback,
				exc_type.__name__,
				exc_instance
			)
			# raise exc_type(message)
			print(exc_type(message))
		finally:
			pass

	return handle_problems


def dict_to_json(t_dict):
	str_json = json.dumps(t_dict, indent=1)
	return str_json


def json_to_dict(json_file):
	str_t = read_file(json_file)
	return json.loads(str_t)


def dict_to_json_file(t_dict, file_path):
	with open(file_path, 'w') as f:
		json.dump(t_dict, f)


def is_string(s):
	return isinstance(s, str)


def is_string_list(s):
	if isinstance(s, list):
		for i in s:
			if not is_string(i):
				return False
		return True
	else:
		return False


def exe_shell(cmd):
	exec_shell = IadsLocalCmdExecuter()
	return exec_shell.run_one_shell_cmd_return_str(cmd)


def search_regex_strings(src_str, reg):
	if is_string_list([src_str, reg]):
		result = re.findall(reg, src_str)
		return result
	else:
		print("src_str is not string!")
		return None


def search_regex_strings_column(src_str, reg, split_str, column):
	if is_string_list([src_str, reg, split_str]):
		result = re.findall(reg, src_str, re.M)
		re_list = []
		for line in result:
			list_re = line.split(split_str)
			re_list.append(list_re[column].strip())
		return re_list
	else:
		print("src_str is not string!")
		return None


def search_regex_one_line_string_column(src_str, reg, split_str, column):
	if is_string_list([src_str, reg, split_str]):
		result = re.findall(reg, src_str, re.M)
		if result:
			list_re = result[0].split(split_str)
			return list_re[column].strip()
		else:
			return None
	else:
		print("src_str is not string!")
		return None


def get_match_sub_string(src_str, reg_str):
	if is_string_list([src_str, reg_str]):
		return re.search(reg_str, src_str).group(0)


def read_file(file_path):
	if os.path.exists(file_path) and os.path.isfile(file_path):
		with open(file_path) as fp:
			try:
				s_t = fp.read()
			except Exception:
				return "-9999"
	else:
		print("file not exists or path is not a file!")
		return "-9999"
	return s_t


def write_file(file_path, buf):
	if os.path.exists(file_path) and os.path.isfile(file_path):
		with open(file_path) as fp:
			try:
				fp.write(buf)
			except Exception:
				return "-9999"
	else:
		print("file not exists or path is not a file!")
		return "-9999"


def list_dir_all_files(path):
	return os.listdir(path)


def list_dir_normal_files(path):
	files = os.listdir(path)
	result = []
	for i in files:
		file_path = os.path.join(path, i)
		if os.path.isfile(file_path):
			result.append(i)
	return result


def path_join(path1, path2):
	return os.path.join(path1, path2)


def get_main_path():
	dir_name, file_name = os.path.split(os.path.abspath(sys.argv[0]))
	return dir_name


def bin_exists(bin_name):
	result = os.environ["PATH"].split(":")
	import stat
	for path_ in result:
		bin_path = pjoin(path_, bin_name)
		if os.path.exists(bin_path):
			if os.access(bin_path, os.X_OK):
				return True
			else:
				try:
					os.chmod(bin_path, stat.S_IXUSR)
				except Exception:
					return False
		else:
			return False


def check_unexists_tools():
	unexists_list = []
	for i in check_list:
		if not bin_exists(i):
			unexists_list.append(i)
	return unexists_list


def copy_tools():
	exes = ["sas2ircu", "sas3ircu", "storcli", ]
	main_path = get_main_path()
	for i in exes:
		shutil.copyfile(os.path.join(main_path, "tools/%s" % i), os.path.join("/bin", i))
		os.chmod("/bin/%s" % i, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)


def rm_tools():
	exes = ["sas2ircu", "sas3ircu", "storcli", ]
	for i in exes:
		file_path = os.path.join("/bin", i)
		if os.path.exists(file_path):
			os.remove(file_path)


def get_os_dev():
	df = exe_shell("df|grep /boot|awk '{print$1}'|sed 's/[0-9]*//g'")
	if df is not None:
		return df.strip()
	else:
		return None
