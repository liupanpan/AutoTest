#!/usr/bin/python
import os
import sys
import time
import errno
import serial
import paramiko
import hashlib
import random
import subprocess
import thread

from datetime import datetime
from xml.etree.ElementTree import ElementTree, Element, dump
from argparse import ArgumentParser

# constants
ENTER = chr(13)
ON = 1
OFF = 0

PLUG_1 = 0
PLUG_2 = 1
PLUG_3 = 2
PLUG_4 = 3
MAX_NUM_OF_ATTEMPTS = 5
UART_BAUD_RATE = 115200
DELAY_1 = 1
DELAY_2 = 2
DELAY_3 = 3
DELAY_4 = 4
DELAY_5 = 5
SERIAL = 0
PLUG_IDX = 1
RUNNING_DUT_DIR = '../running_duts'
TEST_RESULT_DIR = '../test_results'
PROFILE_COMMON = 'common'
PROFILE_TV = 'tv'
PROFILE_MOBILE = 'mobile'
ARCH_ARM = 'arm'
ARCH_ARM64 = 'arm64'
ARCH_X86 = 'x86'
DISP_X11 = 'x11'
DISP_WAYLAND = 'wayland'
SVR_PUBLIC = 'public'
SVR_RSA = 'rsa'
SVR_SPIN = 'spin'
CONN_UTP = 'eth0'
CONN_WLAN = 'wlan0'
# variables
cwd = '' 
test_dut_idx = None
ttyACM = ''
username = 'root'
password = 'tizen'


# Configure DUTs
#You can find the serial number of USB-Switch with command below.
# $ sudo clewarecontrol -l
usb_switch_serials = [ 
'650014',
]

#Please configure "number of dut" properly.
num_of_dut = 2

duts = [ 
{'name' : 'dut0',
'uart' : '/dev/ttyUSB0',
'dc_supl' : (usb_switch_serials[0],PLUG_1), 
'ip_addr' : '192.168.10.10'},

{'name' : 'dut1',
'uart' : '/dev/ttyUSB1',
'dc_supl' : (usb_switch_serials[0],PLUG_4), 
'ip_addr' : '192.168.10.11'},

{'name' : 'dut2',
'uart' : '/dev/ttyUSB2',
'dc_supl' : (usb_switch_serials[0],PLUG_3), 
'ip_addr' : '192.168.10.12'},

{'name' : 'dut3',
'uart' : '/dev/ttyUSB3',
'dc_supl' : (usb_switch_serials[0],PLUG_2), 
'ip_addr' : '192.168.10.13'},
]

# Configure Test
wait_time_for_boot = 16

boot_tcs = [ 
{'profile' : PROFILE_COMMON,
'arch_type': ARCH_ARM,
'disp_svr' : DISP_X11,
'testcases' : [
{'name' : 'dbus_is_running',
'grep_key' : 'dbus', 
'pattern' : '/usr/bin/dbus-daemon'},
{'name' : 'enlightenment_is_running',
'grep_key' : 'enlightenment', 
'pattern' : '/usr/bin/enlightenment'},
{'name' : 'Xorg_is_running',
'grep_key' : 'Xorg', 
'pattern' : '/usr/bin/Xorg'},
{'name' : 'bluetooth_is_running',
'grep_key' : 'bluetooth', 
'pattern' : '/lib/bluetooth/bluetoothd'},
{'name' : 'media-server_is_running',
'grep_key' : 'media-server', 
'pattern' : '/usr/bin/media-server'},
{'name' : 'security-server_is_running',
'grep_key' : 'security-server', 
'pattern' : '/usr/bin/security-server'},
{'name' : 'ofono_is_running',
'grep_key' : 'ofono', 
'pattern' : '/usr/sbin/ofonod'},
]
},
{'profile' : PROFILE_COMMON,
'arch_type' : ARCH_ARM,
'disp_svr' : DISP_WAYLAND, 
'testcases' : [
{'name' : 'dbus_is_running',
'grep_key' : 'dbus', 
'pattern' : '/usr/bin/dbus-daemon'},
{'name' : 'bluetooth_is_running',
'grep_key' : 'bluetooth', 
'pattern' : '/lib/bluetooth/bluetoothd'},
{'name' : 'media-server_is_running',
'grep_key' : 'media-server', 
'pattern' : '/usr/bin/media-server'},
{'name' : 'security-server_is_running',
'grep_key' : 'security-server', 
'pattern' : '/usr/bin/security-server'},
{'name' : 'ofono_is_running',
'grep_key' : 'ofono', 
'pattern' : '/usr/sbin/ofonod'},
]
},
{'profile' : PROFILE_TV, 
'arch_type': ARCH_ARM,
'disp_svr' : DISP_X11,
'testcases' : [
{'name' : 'dbus_is_running',
'grep_key' : 'dbus', 
'pattern' : '/usr/bin/dbus-daemon'},
{'name' : 'enlightenment_is_running',
'grep_key' : 'enlightenment', 
'pattern' : '/usr/bin/enlightenment'},
{'name' : 'Xorg_is_running',
'grep_key' : 'Xorg', 
'pattern' : '/usr/bin/Xorg'},
{'name' : 'bluetooth_is_running',
'grep_key' : 'bluetooth', 
'pattern' : '/lib/bluetooth/bluetoothd'},
{'name' : 'media-server_is_running',
'grep_key' : 'media-server', 
'pattern' : '/usr/bin/media-server'},
{'name' : 'security-server_is_running',
'grep_key' : 'security-server', 
'pattern' : '/usr/bin/security-server'},
{'name' : 'ofono_is_running',
'grep_key' : 'ofono', 
'pattern' : '/usr/sbin/ofonod'},
]
},
{'profile' : PROFILE_MOBILE,
'arch_type': ARCH_ARM,
'disp_svr' : DISP_X11,
'testcases' : [
{'name' : 'dbus_is_running',
'grep_key' : 'dbus', 
'pattern' : '/usr/bin/dbus-daemon'},
{'name' : 'enlightenment_is_running',
'grep_key' : 'enlightenment', 
'pattern' : '/usr/bin/enlightenment'},
{'name' : 'Xorg_is_running',
'grep_key' : 'Xorg', 
'pattern' : '/usr/bin/Xorg'},
{'name' : 'bluetooth_is_running',
'grep_key' : 'bluetooth', 
'pattern' : '/lib/bluetooth/bluetoothd'},
{'name' : 'media-server_is_running',
'grep_key' : 'media-server', 
'pattern' : '/usr/bin/media-server'},
{'name' : 'security-server_is_running',
'grep_key' : 'security-server', 
'pattern' : '/usr/bin/security-server'},
{'name' : 'ofono_is_running',
'grep_key' : 'ofono', 
'pattern' : '/usr/sbin/ofonod'},
]
},
]

# functions
def binary_url_factory(profile,arch_type,disp_type,svr_type):

http = 'http://'

public_url = 'download.tizen.org'
public_common_url = http+public_url\
+'/snapshots/tizen/common/latest/images/'
public_tv_url = http+public_url\
+'/snapshots/tizen/tv/latest/images/'
public_mobile_url = http+public_url\
+'/snapshots/tizen/mobile/latest/images/' 

if profile == PROFILE_COMMON and arch_type == ARCH_ARM \
and disp_type == DISP_X11 and svr_type == SVR_PUBLIC:

return (public_common_url\
+'arm-x11/common-boot-armv7l-odroidu3/',
public_common_url+'arm-x11/common-x11-3parts-armv7l-odroidu3/')

if profile == PROFILE_COMMON and arch_type == ARCH_ARM \
and disp_type == DISP_WAYLAND and svr_type == SVR_PUBLIC:

return (public_common_url\
+'arm-wayland/common-boot-armv7l-odroidu3/',\
public_common_url\
+'arm-wayland/common-wayland-3parts-armv7l-odroidu3/')

if profile == PROFILE_TV and arch_type == ARCH_ARM \
and disp_type == DISP_X11 and svr_type == SVR_PUBLIC:

return (None,
public_tv_url+'arm-x11/tv-x11-3parts-armv7l-odroidu3/')

if profile == PROFILE_MOBILE and arch_type == ARCH_ARM \
and disp_type == DISP_X11 and svr_type == SVR_PUBLIC:

return (None,
public_mobile_url+'arm-x11/mobile-x11-3parts-armv7l-odroidu3/')

else:
raise RuntimeError('Incorrect parameters..('\
+profile+','+arch_type+','+disp_type+','+svr_type+')')

def copy_latest_bins(profile,arch_type,disp_type,svr_type,build_id):
os.system('echo "Copy latest bins from download server..."')
boot_url,platform_url = binary_url_factory(profile,arch_type,\
disp_type,svr_type)

wget_cmd = "wget -r -np -A.tar.gz "
global cwd

hash_object = hashlib.sha1(build_id)
cwd = str(hash_object.hexdigest())

os.mkdir(cwd)
os.chdir(cwd)

if boot_url != None:
os.system(wget_cmd+boot_url)
if platform_url != None:
os.system(wget_cmd+platform_url)

os.system('find . -type f -name "*.tar.gz" -exec mv {} ./ \\;')
os.system('ls -alF | grep ^d | awk \'{print $NF}\' | xargs rm -rf')

def get_available_dut():
if not os.path.isdir(RUNNING_DUT_DIR):
os.mkdir(RUNNING_DUT_DIR)
for i in range(0,num_of_dut):
try: 
f = open(RUNNING_DUT_DIR+'/dut'+str(i),'r')
f.close()
except IOError:
f = open(RUNNING_DUT_DIR+'/dut'+str(i),'w')
f.close()
global test_dut_idx
test_dut_idx = i
break
else:
clean_test_bins()
raise RuntimeError("There's no DUT available!")
os.system('echo "DUT'+str(test_dut_idx)+' is available!"')
os.system('echo "Wait '+str(DELAY_3*test_dut_idx)+' seconds..."')
time.sleep(DELAY_3*test_dut_idx)
return duts[test_dut_idx]

def return_dut_resource():
global test_dut_idx
global ttyACM
os.system('rm -rf '+RUNNING_DUT_DIR+'/dut'+str(test_dut_idx))
os.system('rm -rf '+RUNNING_DUT_DIR+'/'+ttyACM)

def init_uart(uart_tty):
os.system('echo "Initialize UART"')
try:
ser = serial.Serial(uart_tty,UART_BAUD_RATE)
except:
common_exceptions()
raise RuntimeError("Can't open UART.")
return ser

def set_usb_power_switch(plug,on_off,delay):
serial = plug[SERIAL]
index = plug[PLUG_IDX]
if on_off == ON:
print('echo Turn on plug'+str(index+1)\
+', delay : '+str(delay))
else:
print('Turn off plug'+str(index+1)\
+', delay : '+str(delay))
os.system('clewarecontrol -d '\
+serial+' -c 1 -as '+str(index)+' '+str(on_off))
time.sleep(delay)

def start_download():
global ttyACM
os.system('echo "Download binaries..."')
time.sleep(DELAY_1+DELAY_5)
p1 = subprocess.Popen(['ls','/dev'],stdout=subprocess.PIPE)
p2 = subprocess.Popen(['grep','ttyACM'],\
stdin=p1.stdout,stdout=subprocess.PIPE).stdout
data = p2.read().strip().split()

for loop in data:
  try:
f = open(RUNNING_DUT_DIR+'/'+loop,'r')
f.close()
except IOError:
f = open(RUNNING_DUT_DIR+'/'+loop,'w')
f.close()
ttyACM = loop
break
else:
common_exceptions()
raise RuntimeError("Can't find ttyACM")

p2.close()
print(data)

result = os.system('lthor -d /dev/'+ttyACM+' *.tar.gz')
if result != 0:
common_exceptions()
raise RuntimeError("Failed to download binaries")
os.system('rm -rf '+RUNNING_DUT_DIR+'/'+ttyACM)

def print_boot_up_tizen():
os.system('echo "Boot up tizen........"')
for i in range(0,wait_time_for_boot):
os.system('echo "....Wait '\
+str(wait_time_for_boot-i)+' seconds ....."')
time.sleep(DELAY_1)
print ('\n')

def login_shell_uart():
os.system('echo "Log in shell (UART)..."')
ser.write(username+ENTER)
time.sleep(DELAY_1)
ser.write(password+ENTER)
time.sleep(DELAY_2)

def set_dut_config(connector_type,ip):
os.system('echo "Set DUT private IP('+ip+') to make a ssh connection"')
ser.write('ifconfig '+connector_type+' '+ip+ENTER)
time.sleep(DELAY_2)
ser.write('route add default gw 192.168.10.1'+ENTER)

ser.write('systemctl restart sshd.service'+ENTER)
time.sleep(DELAY_3)

def set_host_config():
os.system('echo "Set host private IP(192.168.10.1) '\
+'to make a ssh connection"')
os.system('ifconfig eth1 192.168.10.1')
time.sleep(DELAY_2)

def connect_to_dut_ssh(ip):
os.system('echo "Make a ssh connection now."')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for attempt in range(MAX_NUM_OF_ATTEMPTS):
try:
ssh.connect(ip,username=username,password=password)
except EnvironmentError as enverr:
if enverr.errno == errno.ECONNREFUSED:
time.sleep(DELAY_3)
else:
break
else:
common_exceptions()
raise RuntimeError\
("Maximum number of unsuccessful attempts reached")
return ssh

def clean_test_bins():
global cwd
os.chdir('../')
os.system('rm -rf ./'+cwd)

def common_exceptions():
set_usb_power_switch(test_dut['dc_supl'],OFF,1)
return_dut_resource()
clean_test_bins()

def check_command_result(test_name,grep_key,correct_pattern):
result = False
stdin,stdout,stderr = ssh.exec_command('ps -ax | grep '+grep_key)
for line in stdout:
if line.find(correct_pattern) >= 0:
result = True
break
print(test_name+' == '+str(result))
return result

def apply_indent(elem,level = 0):
indent = '\n' + level * ' '
if len(elem):
if not elem.text or not elem.text.strip():
elem.text = indent + ' '
if not elem.tail or not elem.tail.strip():
elem.tail = indent
for elem in elem:
apply_indent(elem,level+1)
if not elem.tail or not elem.tail.strip():
elem.tail = indent
else:
if level and (not elem.tail or not elem.tail.strip()):
elem.tail = indent

def check_boot_status(profile,arch_type,disp_svr,build_id):
global boot_tcs
cnt = 0
idx = None
for i in range(len(boot_tcs)):
if boot_tcs[i]["profile"] == profile \
and boot_tcs[i]["arch_type"] == arch_type \
and boot_tcs[i]["disp_svr"] == disp_svr:
idx = i
break
else:
common_exceptions()
raise RuntimeError("Can't find test cases for this profile") 

testsuite = Element("testsuite")
for tc in boot_tcs[idx]["testcases"]:
tc["result"] = check_command_result\
(tc["name"],tc["grep_key"],tc["pattern"])
testcase = Element("testcase")
testcase.attrib["name"]=tc["name"]
if tc["result"] == False:
cnt = cnt+1
testcase.attrib["passed"]=str(tc["result"])

testsuite.append(testcase)
testsuite.attrib["failures"] = str(cnt)
apply_indent(testsuite)
dump(testsuite)

if not os.path.isdir(TEST_RESULT_DIR):
os.mkdir(TEST_RESULT_DIR)

profile_dir = TEST_RESULT_DIR+'/'+profile

if not os.path.isdir(profile_dir):
os.mkdir(profile_dir)

result_dir = profile_dir+'/'+build_id
os.mkdir(result_dir)

ElementTree(testsuite).write(result_dir+'/result.xml')
if cnt > 0:
common_exceptions()
raise RuntimeError\
("Boot failed - Some mandatory processes doesn't exist")

def shutdown_dut():
stdin,stdout,stderr = ssh.exec_command('shutdown now')
time.sleep(DELAY_5)

def transfer_file_sftp(src,dest):
host = test_dut['ip_addr']
port = 22
transport = paramiko.Transport((host,port))

transport.connect(username = username,password = password)
sftp = paramiko.SFTPClient.from_transport(transport)

sftp.put(src,dest)

sftp.close()
def init_wireless_lan():

os.system('wget http://ftp2.halpanet.org/source/_dev/linux-firmware.git/rtlwifi/rtl8192cufw_TMSC.bin')

ser.write('echo sdb > /sys/class/usb_mode/usb0/funcs_fconf'+ENTER)
time.sleep(DELAY_1)
ser.write('echo 1 > /sys/class/usb_mode/usb0/enable'+ENTER)
time.sleep(DELAY_1)
ser.write('systemctl restart sdbd.service'+ENTER)
time.sleep(DELAY_2)

os.system('sdb root on')
os.system('sdb push ./rtl8192cufw_TMSC.bin /lib/firmwares/rtlwifi/')

time.sleep(DELAY_2)
ser.write("echo 'ctrl_interface=/var/run/wpa_supplicant' > ~/wpa.conf"+ENTER)
time.sleep(DELAY_1)
ser.write("echo 'update_config=1' >> ~/wpa.conf"+ENTER)
time.sleep(DELAY_1)

time.sleep(DELAY_2)
ser.write('wpa_supplicant -B -i wlan0 -c ~/wpa.conf'+ENTER)
time.sleep(DELAY_2)
ser.write('wpa_cli -iwlan0 scan'+ENTER)
time.sleep(DELAY_2)
ser.write('wpa_cli -iwlan0 scan_results'+ENTER)
time.sleep(DELAY_2)

def send_enter_via_serial(cnt):
for i in range(cnt):
ser.write(ENTER)
time.sleep(0.1)
ser.write('thordown'+ENTER)

if __name__ == '__main__':
parser = ArgumentParser()
parser.add_argument("profile",
help="Tizen profile what you want to test.(common,tv,mobile)",
type=str)
parser.add_argument("arch_type",
help="Architecture what you want to test.(arm,arm64)",
type=str)
parser.add_argument("disp_svr_type",
help="Display_server_type what you want to test.(x11,wayland)",
type=str)
parser.add_argument("download_svr_type",
help="The type of download server that save binaries what you want to test.(public,spin)",
type=str)
parser.add_argument("--buildid",
help="Jenkins buildid.(ex. 2015-01-01_01-00-00)",
type=str)

args = parser.parse_args()

profile = args.profile
arch_type = args.arch_type
disp_svr_type = args.disp_svr_type
download_svr_type = args.download_svr_type
jenkins_buildid = None

if args.buildid:
jenkins_buildid = args.buildid
else:
dt = datetime.now()
jenkins_buildid = dt.strftime('%Y-%m-%d_%H-%M-%S')

#Copy latest bins
copy_latest_bins(profile,arch_type,\
disp_svr_type,download_svr_type,jenkins_buildid)

#Find an available DUT
test_dut = get_available_dut();

#Initialize UART
ser = init_uart(test_dut['uart'])

thread.start_new_thread(send_enter_via_serial,(30,))

#Turn on Odroid U3
set_usb_power_switch(test_dut['dc_supl'],OFF,DELAY_1)
set_usb_power_switch(test_dut['dc_supl'],ON,DELAY_1)

#Start Download
start_download()

#Boot up tizen
print_boot_up_tizen()

#log in shell via UART
login_shell_uart()

#init wireless lan
#init_wireless_lan()

#Set DUT configuration (Odroid U3)
set_dut_config(CONN_UTP,test_dut['ip_addr'])
#set_dut_config(CONN_WLAN,test_dut['ip_addr'])

#Set host configuration
set_host_config()

#Make a ssh connection
ssh = connect_to_dut_ssh(test_dut['ip_addr'])

#Execute cmd (ps -ax | grep process_name)
check_boot_status(profile,arch_type,disp_svr_type,jenkins_buildid)

#shutdown DUT before turn off pwr
shutdown_dut()

#Close ssh connection
ssh.close()

#Close UART connection
ser.close()

#Turn off odroid U3
set_usb_power_switch(test_dut['dc_supl'],OFF,DELAY_1)

#Return DUT resource for next test
return_dut_resource()

#Clean test binaries
clean_test_bins()
