# coding=utf-8

import paramiko


class SSHRemoteCmd:
    def __init__(self, hostname=None, username=None, password=None, timeout=None):
        # paramiko.util.log_to_file('ssh_remote_cmd.log')

        self.hostname = hostname
        self.username = username
        self.password = password

        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        s.connect(hostname=self.hostname, username=self.username, password=self.password, timeout=timeout)
        self.session = s
        self.sftp = None

    def __del__(self):
        if hasattr(self, 'sftp') and self.sftp is not None:
            self.sftp.close()
        if hasattr(self, 'session'):
            self.session.close()

    def run(self, cmd_u, myinput=None, timeout=60):
        stdin, stdout, stderr = self.session.exec_command(cmd_u, timeout=timeout)
        if myinput:
                stdin.write(myinput)

        ret = stdout.channel.recv_exit_status()
        return stdout, ret

    def run2(self, cmd_u, myinput=None, timeout=60):
        stdin, stdout, stderr = self.session.exec_command(cmd_u, timeout=timeout)
        if myinput:
                stdin.write(myinput)

        ret = stdout.channel.recv_exit_status()
        return ret, stdout.read(), stderr.read()

    def open_ftp(self):
        self.sftp = self.session.open_sftp()
        return self.sftp

    def path_exists(self, path):
        try:
            self.sftp.stat(path)
        except IOError:
            return False
        return True

    @staticmethod
    def exe_shell(hostname, command, username="root", password="000000"):
        cmd_t = SSHRemoteCmd(hostname, username, password)
        out_t, err_t = cmd_t.run(command)
        return "".join(out_t.readlines())

# if __name__ == "__main__":
#    print(SSHRemoteCmd.exe_shell("192.168.0.65", "cat /proc/cpuinfo"))
