# coding=utf-8
from linux.storage.disk import Disk
import json


def show_disk_info():
	pass


def show_err_disk():
	err_disks_dict = Disk.get_err_disk_dict()
	err_disk_json = json.dumps(err_disks_dict, indent=1)
	print(err_disk_json)