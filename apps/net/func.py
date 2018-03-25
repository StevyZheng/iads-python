# coding = utf-8
try:
	from io import StringIO
except ImportError:
	from StringIO import StringIO
import os
from os.path import join as pjoin
import ConfigParser
import netifaces
from linux import bin_exists, exe_shell, search_regex_strings

conf_path = "/etc/sysconfig/network-scripts"


class NetConfigParser(ConfigParser):
	def read(self, filename):
		try:
			text = open(filename, "r").read()
		except IOError:
			pass
		else:
			file_t = StringIO("[stevy]\n" + text)
			self.readfp(file_t, filename)
	
	def write(self, filename):
		pass
		

def get_net_conf():
	interfaces = [x for x in netifaces.interfaces() if "e" in x]
	net_dict = {}
	for interface in interfaces:
		conf = netifaces.ifaddresses(interface)
		eth_num = netifaces.AF_INET
		link_num = netifaces.AF_LINK
		if eth_num in conf:
			if "addr" in conf[eth_num]:
				net_dict[interface]["addr"] = conf[eth_num][0]["addr"]
			if "netmask" in conf[eth_num]:
				net_dict[interface]["netmask"] = conf[eth_num][0]["netmask"]
			if "broadcast" in conf[eth_num]:
				net_dict[interface]["broadcast"] = conf[eth_num][0]["broadcast"]
		if link_num in conf:
			if "addr" in conf[eth_num]:
				net_dict[interface]["mac"] = conf[link_num][0]["addr"]
		interface_file = pjoin(conf_path, "ifcfg-%s" % interface)
		if os.path.exists(interface_file):
			config = NetConfigParser()
			config.read(interface_file)
			net_dict[interface]["bootproto"] = config.get("stevy", "BOOTPROTO")
			net_dict[interface]["uuid"] = config.get("stevy", "UUID")
			net_dict[interface]["onboot"] = config.get("stevy", "ONBOOT")
	return net_dict


def get_net_interface():
	pass
