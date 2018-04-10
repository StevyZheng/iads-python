# coding = utf-8
try:
	from io import StringIO
except ImportError:
	from StringIO import StringIO
import os
from os.path import join as pjoin
from ConfigParser import *
import netifaces
from linux import bin_exists, exe_shell, search_regex_strings

conf_path = "/etc/sysconfig/network-scripts"


class NetConfigParser(ConfigParser):
	def read(self, filenames):
		"""Read and parse a filename or a list of filenames.

		Files that cannot be opened are silently ignored; this is
		designed so that you can specify a list of potential
		configuration file locations (e.g. current directory, user's
		home directory, systemwide directory), and all existing
		configuration files in the list will be read.  A single
		filename may also be given.

		Return list of successfully read files.
		"""
		if isinstance(filenames, basestring):
			filenames = [filenames]
		read_ok = []
		for filename in filenames:
			try:
				fp = open(filename)
			except IOError:
				continue
			else:
				file_t = StringIO("[%s]\n" % DEFAULTSECT) + fp
				self._read(file_t, filename)
				fp.close()
				read_ok.append(filename)
		return read_ok

	def write(self, fp):
		"""Write an .ini-format representation of the configuration state."""
		if self._defaults:
			for (key, value) in self._defaults.items():
				fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
				fp.write("\n")
		for section in self._sections:
			for (key, value) in self._sections[section].items():
				if key == "__name__":
					continue
				if (value is not None) or (self._optcre == self.OPTCRE):
					key = " = ".join((key, str(value).replace('\n', '\n\t')))
				fp.write("%s\n" % key)
			fp.write("\n")


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
