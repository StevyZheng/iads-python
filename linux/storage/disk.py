# coding = utf-8
import linux
import re
import json
from linux import try_catch


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

	@staticmethod
	def map_disk_wwn_hctl(diskname):
		lsscsi = linux.exe_shell("lsscsi -w |grep /dev/|awk '{print$1,$3,$4}'")
		for i in lsscsi.splitlines():
			split_t = i.split(" ")
			if diskname in split_t[2]:
				return {
					"hctl": split_t[0],
					"wwn": split_t[1],
					"dev_name": split_t[2]
				}
			else:
				return None

	@staticmethod
	def get_from_sas_disk_smart_i_str(disk_name):
		return linux.exe_shell("smartctl -i /dev/%s" % disk_name)

	@staticmethod
	def get_from_sas_disk_simple_attr(disk_name):
		smart = Disk.get_from_sas_disk_smart_i_str(disk_name)
		model = linux.search_regex_one_line_string_column(smart, "(?:Device Model|Product):.+", ":", 1).strip()
		sn = linux.search_regex_one_line_string_column(smart, "Serial (?:N|n)umber.+", ":", 1).strip()
		vendor = linux.search_regex_one_line_string_column(smart, "(?:SATA Ver|Vendor).+", ":", 1).strip()
		return {
			"name": disk_name,
			"model": model,
			"sn": sn,
			"vendor": vendor
		}

	@staticmethod
	def get_all_disk():
		disks = []
		disks_lines = linux.exe_shell("lsblk -o NAME,VENDOR|grep -P '^sd.*[A-Z]'")
		for line in disks_lines.splitlines():
			disk_t = line.split()
			if len(disk_t) < 1 and "LSI" not in disk_t[1]:
				disks.append(disk_t[0])
		ds = []
		for i in disks:
			d_t = DiskFromLsiSas3("", i)
			d_t.fill_attrs()
			ds.append(d_t)
		return ds

	@staticmethod
	def __if_smart_err(disk_oj):
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
			pass

	@staticmethod
	def get_err_disk_dict():
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


class DiskFromLsiSas3(Disk):
	def __init__(self, sn, name):
		Disk.__init__(self)
		self.sn = sn
		self.dev_name = name

	def fill_attrs(self):
		smart_str = linux.exe_shell("smartctl -a /dev/%s" % self.dev_name)
		smartx_str = linux.exe_shell("smartctl -x /dev/%s" % self.dev_name)
		self.smart = smartx_str
		self.model = linux.search_regex_one_line_string_column(smart_str, "(?:Device Model|Product):.+", ":", 1).strip()
		self.fw = linux.search_regex_one_line_string_column(smart_str, "(?:Firmware|Revision).+", ":", 1).strip()
		self.vendor = linux.search_regex_one_line_string_column(smart_str, "(?:ATA|Vendor).+", ":", 1).strip()
		self.sn = linux.search_regex_one_line_string_column(smart_str, "Serial (?:N|n)umber.+", ":", 1).strip()
		self.wwn = self.map_disk_wwn_hctl(self.dev_name)["wwn"]
		self.hctl = self.map_disk_wwn_hctl(self.dev_name)["hctl"]

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
				self.age["start_stop_count"] = linux.search_regex_one_line_string_column(self.smart, ".+start-stop.+", ":", 1)
				max_gb = max(self.smart_attr["read"]["byte10_9"], self.smart_attr["write"]["byte10_9"], self.smart_attr["verify"]["byte10_9"])
				self.age["data_gb"] = str(max_gb)

		if "SATA" in smart_str:
			self.type = "SATA"
			dict_tmp = linux.search_regex_strings(smart_str, "^( |[0-9])+.+[0-9]+ .+0x.+(In_the_past|-|FAILING_NOW) +[0-9]+")
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
				self.age["start_stop_count"] = self.smart_attr["Start_Stop_Count"]
				self.age["power_on_hours"] = self.smart_attr["Power_On_Hours"]

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
		DiskFromLsiSas3.__init__(self, sn, name)
