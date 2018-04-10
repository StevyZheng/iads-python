# coding=utf-8
from linux.storage.disk import Disk
import json
from tabulate import tabulate

SAS_LIMIT_COUNT = 10
SAS_LIMIT_GB = 1024
SATA_LIMIT_HOURS = 10


def show_disk_info(dev_name):
	disk_dict = Disk.get_dev_attr_dict(dev_name)
	json_str = json.dumps(disk_dict, indent=1)
	print(json_str)


def show_disk_list():
	disk_list = Disk.get_all_disk()
	disk_header = ["H:C:T:L", "name", "model", "fw", "type"]
	disk_data = []
	for ds in disk_list:
		tmp = [ds.hctl, ds.dev_name, ds.model, ds.fw, ds.type]
		disk_data.append(tmp)
	print(tabulate(disk_data, disk_header, tablefmt="fancy_grid", stralign="center", numalign="center"))


def show_err_smart_disk():
	err_disks_dict = Disk.get_err_disk_dict()
	err_disk_json = json.dumps(err_disks_dict, indent=1)
	print(err_disk_json)


def show_overage_disk():
	disks = Disk.get_all_disk()
	over_sas_disk, over_sata_disk = Disk.get_over_agelimit_disks(disks)
	sas_header = ["name", "startCount", "data(GB)"]
	sata_header = ["name", "startCount", "hours"]
	sas_data = []
	sata_data = []
	for disk in over_sas_disk:
		sas_data.append([disk.dev_name, disk.age["start_stop_count"], disk.age["data_gb"]])
	for disk in over_sata_disk:
		sata_data.append([disk.dev_name, disk.age["start_stop_count"], disk.age["power_on_hours"]])
	print("SAS Disk:")
	print(tabulate(sas_data, sas_header, tablefmt="fancy_grid", stralign="center", numalign="center"))
	print("SATA Disk:")
	print(tabulate(sata_data, sata_header, tablefmt="fancy_grid", stralign="center", numalign="center"))


def show_wearout_ssd():
	disks = Disk.get_wearout_ssd_status()
	if disks is None:
		print("Cannot find SSD.")
		return
	ssd_wearout_header = ["name", "wearout"]
	ssd_wearout_data = []
	for key in disks:
		ssd_wearout_data.append([key, disks[key]])
	print(tabulate(ssd_wearout_data, ssd_wearout_header, tablefmt="fancy_grid", stralign="center", numalign="center"))
