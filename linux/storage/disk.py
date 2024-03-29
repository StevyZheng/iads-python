# coding = utf-8
import os
import linux
import re
import json
from linux import try_catch

SAS_LIMIT_COUNT = 10
SAS_LIMIT_GB = 1024
SATA_LIMIT_HOURS = 10
SSD_WEAROUT_LIMIT = 99
SATA_SMART_ERROR_LIST = [
	"Reallocated_Sector_Ct",
	"Spin_Retry_Count",
	"End-to-End_Error",
	"High_Fly_Writes",
	"Current_Pending_Sector",
	"UDMA_CRC_Error_Count"
]


class Disk(object):
	def __init__(self):
		self.model = ""
		self.vendor = ""
		self.fw = ""
		self.sn = ""
		self.wwn = ""
		self.hctl = ""
		self.dev_name = ""
		self.smart = ""
		self.type = ""
		self.smart_attr = {}
		self.age = {}
		self.flash = False

	@staticmethod
	def map_disk_wwn_hctl(diskname):
		""" map wwn and H:C:T:L from dev_name """
		lsscsi = linux.exe_shell("lsscsi -w |grep /dev/|awk '{print$1,$3,$4}'")
		for i in lsscsi.splitlines():
			split_t = i.split(" ")
			if diskname in split_t[2]:
				return {
					"hctl": split_t[0],
					"wwn": split_t[1],
					"dev_name": split_t[2]
				}
		return None

	@staticmethod
	def get_from_sas_disk_smart_i_str(disk_name):
		return linux.exe_shell("smartctl -i /dev/%s" % disk_name)

	@staticmethod
	def get_from_sas_disk_simple_attr(disk_name):
		smart = Disk.get_from_sas_disk_smart_i_str(disk_name)
		model = linux.search_regex_one_line_string_column(smart, "(?:Device Model|Product):.+", ":", 1).strip()
		sn = linux.search_regex_one_line_string_column(smart, "Serial (?:N|n)umber.+", ":", 1).strip()
		vendor = linux.search_regex_one_line_string_column(smart, "(?:SATA Ver|Vendor).+", ":", 1).split()[0].strip()
		return {
			"name": disk_name,
			"model": model,
			"sn": sn,
			"vendor": vendor
		}

	@staticmethod
	def get_all_disk():
		""" return all disk object list from hba and chipset. """
		disks = []
		disks_lines = linux.exe_shell("lsblk -o NAME,VENDOR|grep -P '^sd.*[A-Z]'")
		for line in disks_lines.splitlines():
			disk_t = line.split()
			if len(disk_t) > 1 and "LSI" not in disk_t[1]:
				disks.append(disk_t[0])
		ds = []
		for i in disks:
			d_t = DiskFromLsiSas3("", i)
			d_t.fill_attrs()
			ds.append(d_t)
		return ds

	@staticmethod
	def get_dev_attr_dict(dev_name):
		i = DiskFromLsiSas3("", dev_name)
		i.fill_attrs()
		return {
			"dev": i.dev_name,
			"model": i.model,
			"fw": i.fw,
			"SN": i.sn,
			"type": i.type,
			"vendor": i.vendor,
			"smart": i.smart_attr,
			"hctl": i.hctl,
			"wwn": i.wwn,
			"age": i.age,
			"is_ssd": str(i.flash)
		}

	@staticmethod
	def __if_smart_err(disk_oj):
		""" return True if smart info of disk_oj has error, else return False """
		if "SAS" in disk_oj.smart:
			if int(disk_oj.smart_attr["channel0Error"]["Invalid DWORD count"]) > 0 or \
							int(disk_oj.smart_attr["channel0Error"]["Running disparity error count"]) > 0 or \
							int(disk_oj.smart_attr["channel0Error"]["Loss of DWORD synchronization"]) > 0 or \
							int(disk_oj.smart_attr["channel0Error"]["Phy reset problem"]) > 0 or \
							int(disk_oj.smart_attr["channel1Error"]["Invalid DWORD count"]) > 0 or \
							int(disk_oj.smart_attr["channel1Error"]["Running disparity error count"]) > 0 or \
							int(disk_oj.smart_attr["channel1Error"]["Loss of DWORD synchronization"]) > 0 or \
							int(disk_oj.smart_attr["channel1Error"]["Phy reset problem"]) > 0:
				return True
			else:
				return False
		if "SATA" in disk_oj.smart:
			if "No Errors Logged" not in disk_oj.smart:
				return False
			for attr_ in SATA_SMART_ERROR_LIST:
				if disk_oj.smart_attr[attr_]["RAW_VALUE"] > 0:
					return False
			return True

	@staticmethod
	def get_over_agelimit_disks(disk_list):
		""" return sas and sata disk list witch start_stop_hours/count or data is over the limit """
		over_sas_disk = []
		over_sata_disk = []
		for disk in disk_list:
			if disk.type == "SAS":
				if int(disk.age["start_stop_count"]) > SAS_LIMIT_COUNT or float(disk.age["data_gb"]) > SAS_LIMIT_GB:
					over_sas_disk.append(disk)
			if disk.type == "SATA":
				if int(disk.age["start_stop_count"]) > SAS_LIMIT_COUNT or int(
						disk.age["power_on_hours"]) > SATA_LIMIT_HOURS:
					over_sata_disk.append(disk)
		return over_sas_disk, over_sata_disk

	@staticmethod
	def get_overage_disks_json(disk_list):
		""" get_overage_disks function's json model """
		pass

	@staticmethod
	def get_err_disk_dict():
		""" return disk dict has error """
		err_disk_dict = {}
		disks = Disk.get_all_disk()
		for i in disks:
			if Disk.__if_smart_err(i):
				struct = {
					"dev": i.dev_name,
					"model": i.model,
					"fw": i.fw,
					"SN": i.sn,
					"type": i.type,
					"vendor": i.vendor,
					"smart": i.smart_attr,
					"hctl": i.hctl,
					"wwn": i.wwn
				}
				err_disk_dict[i.dev_name] = struct
		return err_disk_dict

	@staticmethod
	def get_wearout_ssd_status():
		""" return ssd wearout status dict """
		disks = Disk.get_all_disk()
		ssd_status = {}
		for i in disks:
			tmp = i.get_wearout_status()
			# tmp[0] is dev_name, tmp[1] is wearout %
			if tmp is not None:
				ssd_status[tmp[0]] = tmp[1]
		if len(ssd_status) == 0:
			return None
		return ssd_status


class DiskFromLsiSas3(Disk):
	def __init__(self, sn, name):
		super(DiskFromLsiSas3, self).__init__()
		self.sn = sn
		self.dev_name = name

	def fill_attrs(self):
		smart_str = linux.exe_shell("smartctl -a /dev/%s" % self.dev_name)
		smartx_str = linux.exe_shell("smartctl -x /dev/%s" % self.dev_name)
		self.smart = smartx_str
		try:
			self.model = linux.search_regex_one_line_string_column(smart_str, "(?:Device Model|Product):.+", ":",
			                                                       1).strip()
			self.fw = linux.search_regex_one_line_string_column(smart_str, "(?:Firmware|Revision).+", ":", 1).strip()
			self.vendor = linux.search_regex_one_line_string_column(smart_str, "(?:SATA Ver|Vendor).+", ":", 1).split()[
				0].strip()
			self.sn = linux.search_regex_one_line_string_column(smart_str, "Serial (?:N|n)umber.+", ":", 1).strip()
			map_temp = self.map_disk_wwn_hctl(self.dev_name)
			self.wwn = map_temp["wwn"] if map_temp is not None else ""
			self.hctl = map_temp["hctl"] if map_temp is not None else ""
			rotational = linux.read_file(os.path.join("/sys/block", self.dev_name, "queue/rotational"))
			if rotational.strip() == "0":
				self.flash = True
		except IOError:
			print("%s read_file rotational err." % self.dev_name)

		except Exception:
			print("disk %s is not exists." % self.dev_name)

		# fill in smart_attr
		# ==========================================================================
		# SAS disk
		# smart_attr: {
		#   'channel0Error': {
		#       'Invalid DWORD count': '0',
		#       'Loss of DWORD synchronization': '0',
		#       'Phy reset problem': '0',
		#       'Running disparity error count': '0'
		#   }
		#   'channel1Error': {
		#       'Invalid DWORD count': '0',
		#       'Loss of DWORD synchronization': '0',
		#       'Phy reset problem': '0',
		#       'Running disparity error count': '0'
		#   }
		#   'read': {
		#       'byte10_9': '59036.419',
		#       'correctionAlgorithmInvocations': '414271',
		#       'errorEccByRereadsRewrite': '0',
		#       'errorEccDelayed': '8',
		#       'errorEccFast': '0',
		#       'totalErrorsCorrected': '8',
		#       'totalUncorrectedError': '0'
		#   }
		#   'verify': {
		#       'byte10_9': '59036.419',
		#       'correctionAlgorithmInvocations': '414271',
		#       'errorEccByRereadsRewrite': '0',
		#       'errorEccDelayed': '8',
		#       'errorEccFast': '0',
		#       'totalErrorsCorrected': '8',
		#       'totalUncorrectedError': '0'
		#   }
		#   'write': {
		#       'byte10_9': '59036.419',
		#       'correctionAlgorithmInvocations': '414271',
		#       'errorEccByRereadsRewrite': '0',
		#       'errorEccDelayed': '8',
		#       'errorEccFast': '0',
		#       'totalErrorsCorrected': '8',
		#       'totalUncorrectedError': '0'
		#   }
		# }
		#
		# SATA disk
		# smart_attr: {
		#   'Raw_Read_Error_Rate': {
		#       'ID': '1',
		#       'FLAG': '0x000f',
		#       'VALUE': '074',
		#       'WORST': '063',
		#       'THRESH': '044',
		#       'TYPE': 'Pre-fail',
		#       'UPDATED': 'Always',
		#       'WHEN_FAILED': '-',
		#       'RAW_VALUE': '26816470'
		#   }
		#   'Spin_Up_Time': {
		#       ...(According to the following form)
		#   }
		# }
		#  SATA smart form:
		#  ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
		#   1 Raw_Read_Error_Rate     0x000f   074   063   044    Pre-fail  Always       -       26816470
		#   3 Spin_Up_Time            0x0003   094   094   000    Pre-fail  Always       -       0
		#   4 Start_Stop_Count        0x0032   100   100   020    Old_age   Always       -       314
		#   5 Reallocated_Sector_Ct   0x0033   100   100   036    Pre-fail  Always       -       1
		#   7 Seek_Error_Rate         0x000f   073   060   030    Pre-fail  Always       -       21595176
		#   9 Power_On_Hours          0x0032   096   096   000    Old_age   Always       -       3851
		#  10 Spin_Retry_Count        0x0013   100   100   097    Pre-fail  Always       -       0
		#  12 Power_Cycle_Count       0x0032   100   100   020    Old_age   Always       -       271
		# 184 End-to-End_Error        0x0032   100   100   099    Old_age   Always       -       0
		# 187 Reported_Uncorrect      0x0032   100   100   000    Old_age   Always       -       0
		# 188 Command_Timeout         0x0032   100   100   000    Old_age   Always       -       0
		# 189 High_Fly_Writes         0x003a   100   100   000    Old_age   Always       -       0
		# 190 Airflow_Temperature_Cel 0x0022   064   057   045    Old_age   Always       -       36 (Min/Max 24/40)
		# 191 G-Sense_Error_Rate      0x0032   100   100   000    Old_age   Always       -       0
		# 192 Power-Off_Retract_Count 0x0032   100   100   000    Old_age   Always       -       147
		# 193 Load_Cycle_Count        0x0032   099   099   000    Old_age   Always       -       2690
		# 194 Temperature_Celsius     0x0022   036   043   000    Old_age   Always       -       36 (0 11 0 0 0)
		# 195 Hardware_ECC_Recovered  0x001a   110   099   000    Old_age   Always       -       26816470
		# 197 Current_Pending_Sector  0x0012   100   100   000    Old_age   Always       -       0
		# 198 Offline_Uncorrectable   0x0010   100   100   000    Old_age   Offline      -       0
		# 199 UDMA_CRC_Error_Count    0x003e   200   200   000    Old_age   Always       -       0
		#
		# ===========================================================================
		if "SAS" in smart_str:
			self.type = "SAS"
			smart_str_arr = linux.search_regex_strings(smart_str, " *(?:write:|read:|verify:).+")
			for line in smart_str_arr:
				tmp = line.split()
				dict_tmp = {
					"errorEccFast": tmp[1].strip(),
					"errorEccDelayed": tmp[2].strip(),
					"errorEccByRereadsRewrite": tmp[3].strip(),
					"totalErrorsCorrected": tmp[4].strip(),
					"correctionAlgorithmInvocations": tmp[5].strip(),
					"byte10_9": tmp[6].strip(),
					"totalUncorrectedError": tmp[7].strip()
				}
				self.smart_attr[tmp[0].replace(":", " ").strip()] = dict_tmp
			smart_str_arr = linux.search_regex_strings(
				self.smart,
				"(?:Invalid DWORD|Running disparity|Loss of DWORD|Phy reset problem).+=.+"
			)
			i = 0
			dict_tmp = {}
			for it in smart_str_arr:
				tmp = it.split("=")
				dict_tmp[tmp[0].strip()] = tmp[1].strip()
				if 3 == i:
					self.smart_attr["channel0Error"] = dict_tmp
					dict_tmp = {}
				if 7 == i:
					self.smart_attr["channel1Error"] = dict_tmp
					dict_tmp = {}
				i += 1
			# fill in age
			# 'data_gb' is float number
			# age: {
			#   'start_stop_count': '10',
			#   'data_gb': '5999'
			# }
			if isinstance(self.smart, str) and ("start-stop" in self.smart):
				self.age["start_stop_count"] = linux.search_regex_one_line_string_column(self.smart, ".+start-stop.+",
				                                                                         ":", 1)
				all_gb = float(self.smart_attr["read"]["byte10_9"]) + float(
					self.smart_attr["write"]["byte10_9"]) + float(self.smart_attr["verify"]["byte10_9"])
				self.age["data_gb"] = str(all_gb)

		if "SATA" in smart_str:
			self.type = "SATA"
			dict_tmp = linux.search_regex_strings(smart_str, ".*[0-9]+.+0x.+(?:In_the_past|-|FAILING_NOW) +[0-9]+")
			for line in dict_tmp:
				tmp = line.split()
				dict_tmp = {
					"ID": tmp[0].strip(),
					"FLAG": tmp[2].strip(),
					"VALUE": tmp[3].strip(),
					"WORST": tmp[4].strip(),
					"THRESH": tmp[5].strip(),
					"TYPE": tmp[6].strip(),
					"UPDATED": tmp[7].strip(),
					"WHEN_FAILED": tmp[8].strip(),
					"RAW_VALUE": tmp[9].strip(),
				}
				self.smart_attr[tmp[1]] = dict_tmp

			if "Start_Stop_Count" in self.smart_attr:
				self.age["start_stop_count"] = self.smart_attr["Start_Stop_Count"]["RAW_VALUE"]
				self.age["power_on_hours"] = self.smart_attr["Power_On_Hours"]["RAW_VALUE"]

	def get_wearout_status(self):
		if self.flash is True and "Media_Wearout_Indicator" in self.smart_attr:
			value = self.smart_attr["Media_Wearout_Indicator"]["VALUE"]
			return self.dev_name, value
		else:
			return None

	def to_json(self):
		struct = {
			"dev": self.dev_name,
			"model": self.model,
			"fw": self.fw,
			"SN": self.sn,
			"type": self.type,
			"vendor": self.vendor,
			"smart": self.smart_attr,
			"hctl": self.hctl,
			"wwn": self.wwn
		}
		json_str = json.dumps(struct, indent=1)
		return json_str


class DiskFromLsiSas2(DiskFromLsiSas3):
	def __init__(self, sn, name):
		super(DiskFromLsiSas2, self).__init__(sn, name)


class DiskFromChipset(DiskFromLsiSas3):
	def __init__(self, sn, name):
		super(DiskFromChipset, self).__init__(sn, name)


class DiskFromMegaRaid(Disk):
	def __init__(self, did, name):
		super(DiskFromMegaRaid, self).__init__()
		self.dev_name = name
		self.did = did

	def fill_attrs(self):
		pass
