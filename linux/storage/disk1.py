# coding = utf-8
import os
import json
import re
import threading
from os.path import join as pjoin
import linux
from iadslib.iadsBaseContext import IadsBaseException


class Disk(object):
    def __init__(self):
        self.dev_name = ""
        self.dev = ""
        self.wwn = ""
        self.model = ""
        self.fw = ""
        self.sn = ""
        self.hctl = ""
        self.smart = ""
        self.type = ""
        self.smart_attr = {}
        self.age = {}
        self.flash = False
        self.mega = False

    @classmethod
    def map_disk_wwn_dev_hctl(cls, diskname):
        """ map wwn and H:C:T:L from dev_name """
        path = pjoin("/sys/block", diskname)
        if os.path.exists(path) is False:
            return None
        udevadm = linux.exe_shell("udevadm info -q all -n /dev/%s" % diskname)
        dev = linux.read_file(pjoin(path, "dev"))
        wwn = linux.search_regex_one_line_string_column(udevadm, "ID_WWN=", "=", 1)

    @classmethod
    def scan_disks(cls):
        def thread_func(disk_name):
            pass
        disks = []
        dirs = linux.list_dir_all_files("/sys/block")
        for d in dirs:
            if re.match("sd[a-z]+", d) is not None:
                disks.append(d)
                t = threading.Thread()

    @classmethod
    def _if_raid_volume(cls, model):
        match = re.match(".*9[2-4][0-9]{2}.*", model, re.M | re.I)
        if match is None:
            return False
        else:
            return True


class DirectDisk(Disk):
    def __init__(self, disk_name):
        super(DirectDisk, self).__init__()
        self.dev_name = disk_name

    def fill_attr(self):
        path = pjoin("/sys/block", self.dev_name)
        if os.path.exists(path) is False:
            IadsBaseException("%s is not exists." % path)
        udevadm = linux.exe_shell("udevadm info -q all -n /dev/%s" % self.dev_name).strip()
        self.dev = linux.read_file(pjoin(path, "dev"))
        t_type = linux.search_regex_one_line_string_column(udevadm, "ID_BUS=", "=", 1)
        if t_type == "ata":
            self.type = "sata"
        elif t_type == "scsi":
            self.type = "sas"
        self.wwn = linux.search_regex_one_line_string_column(udevadm, "ID_WWN=", "=", 1)
        self.model = linux.search_regex_one_line_string_column(udevadm, "ID_MODEL=", "=", 1)
        if self.type == "sata":
            self.sn = linux.search_regex_one_line_string_column(udevadm, "ID_SERIAL_SHORT=", "=", 1)
        elif self.type == "sas":
            self.sn = linux.search_regex_one_line_string_column(udevadm, "ID_SCSI__SERIAL=", "=", 1)
        lsscsi_str = linux.exe_shell("lsscsi")
        for line in lsscsi_str:
            if self.dev_name in line:
                line_list = line.split()
                if len(line_list) > 0:
                    self.hctl = line_list[0].strip("[]")
            else:
                IadsBaseException("%s lsscsi has no this device." % self.dev_name)

        self.fw = linux.read_file(pjoin(path, "device", "rev"))
        rotational = linux.read_file(os.path.join(path, "queue/rotational"))
        if rotational.strip() == "0":
            self.flash = True
        self.mega = False

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

        smart_str = linux.exe_shell("smartctl -a /dev/%s" % self.dev_name)
        smartx_str = linux.exe_shell("smartctl -x /dev/%s" % self.dev_name)
        self.smart = smartx_str

        if self.type == "sas":
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

        self.smart_attr = {}
        self.age = {}

        if self.type == "sata":
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


class MegaDisk(Disk):
    pass

