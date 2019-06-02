import base64
import pypyodbc
import xml.etree.ElementTree as ET
import time
import re
import pyexcel as pe
from datetime import timedelta
import datetime
import os
import pathlib
import shutil
import subprocess
import os.path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# This is the class of the framework 
class MyTest:
	# All variables under __init__ will be created whtn "MyTest" calss is called from any test
    def __init__(self, app_name, folder, translation_file):
		# Starting the adb server
        subprocess.call("adb start-server", shell=False)
		# Clear old adb logs 
        subprocess.call(f"adb logcat -c", shell=False)
		# use the app name from the init to create a Test folder 
        self.folder_id = app_name + "_"
		# get the current date and time 
        self.now = datetime.datetime.now()
		# format the date time to desire format 
        self.current_time = self.now.strftime("%m-%d-%y-%H-%M-%S")
        # Create a unique email using app name and current time 
        self.email = self.folder_id + self.current_time + "@comscore.com"
        # Get the current working directory as a string (where this python file is currently located)  
        self.Parent_Dir = str(os.getcwd())
		# Set the directory where translation file is located
        self.translations_path = self.Parent_Dir + '\\' + "_translations"
		# Add the translation file name from the test and translation_file from the test 
        self.translation_excel = self.translations_path + '\\' + translation_file
        # set apk folder path
        self.apk_Path = self.Parent_Dir + '\\' + "_apk"
        # Get current working directory Path
        self.directory = os.getcwd()
		# Create a test directory 
        self.project_dir = self.directory + '\\' + folder
		# CD to the test directory 
        os.chdir(self.project_dir)
        # Create a results(test_log) folder for all test results
        pathlib.Path("results").mkdir(parents=True, exist_ok=True)
        # Setting up the results path for the project
        self.results_path = self.directory + '\\' + folder + "\\" + "results"
        # set the folder name with the date
        self.folder_name = self.folder_id + self.current_time
        # change directory to results
        os.chdir(self.results_path)
        # Create a folder and get folder path
        pathlib.Path(self.folder_name).mkdir(parents=True, exist_ok=True)
        # Root directory path (directory where the test scripts are)
        # Test folder path
        self.folder_path = self.results_path + '\\' + self.folder_name
        # change directory to test folder
        os.chdir(self.folder_path)
        # Set a file name for a test log file
        self.test_log = self.current_time + "_Test_Log.txt"
		# create a test log object 
        self.log_file = self.folder_path + '\\' + self.test_log
		# open a test log file to start writing the logs
        self.logthis = open(self.log_file, 'a', encoding="utf-8")
        # Start adb logs
        self.adb_file = self.current_time + "_adb_Log.txt"
        # Create adb log file and get the variable
        self.adb_log = self.folder_path + '\\' + self.adb_file
		# Open an adb log file to start writing the adb logs
        self.to_adb = open(self.adb_log, 'a', encoding="utf-8")
        # Start adb logs, all adb logs will start writing to the adb file opened above
        self.proc = subprocess.Popen(["adb", "logcat", "-v", "threadtime"], stdout=self.to_adb, stderr=self.to_adb, shell=False)
        # CShared Location
        self.shared_path = "\\\\csvafs01\\public\\SoftwareTesting\\Mobile_Testing\\Automation" + "\\" + folder + "\\" + "results"
		# get the device model and write to the test log file
        self.device_model = subprocess.check_output(f"adb devices -l", shell=False)
		# Output from the above line is in byte so we need to change it to String 
        self.device_model = str(self.device_model, 'UTF-8')
		# Split the String above so that we can do the searching 
        self.push_model_split = self.device_model.split()  # split the output to check device is in the output
        self.logthis.write(f"++++++++ TEST DEVICE INFO +++++++++++\n\n")
		# This is to filter only the device model name that we want from the String 
        for item in self.push_model_split[4:]:
            self.logthis.write(f"{item} ")
        # Get android version and write to the log file
        self.os_version = subprocess.check_output(f"adb shell getprop ro.build.version.release", shell=False)
        self.logthis.write(f"\n\ninit:: Android Version: {self.os_version}")
        # Get API Level
        self.API_level = subprocess.check_output(f"adb shell getprop ro.build.version.sdk ", shell=False)
        self.logthis.write(f"init:: API Level: {self.API_level}\n")
		# Getting the connectivity info, format it and write to the log file 
        try:
            self.SSID = subprocess.check_output(f"adb shell dumpsys netstats | grep -E iface=wlan", shell=False)
            self.SSID = str(self.SSID, 'UTF-8')
            self.SSID = self.SSID.splitlines()[0]
            self.logthis.write(f"init:: Connected SSID: {self.SSID}\n")
            self.logthis.write(f"++++++++ END OF DEVICE INFO +++++++++++\n\n")
        except IndexError:
            self.logthis.write(f"init:: Error getting connected SSID. Please check your wifi conneciton.\n")
            self.logthis.write(f"++++++++ END OF DEVICE INFO +++++++++++\n\n")

    # adb command function with shell is set to False
    def adb(self,command):
        output = subprocess.check_output(command, shell=False)
        return output
	# adb command function with shell is set to TRUE, will need it for adb command with options and flags 
    def adbshell(self,command):
        output = subprocess.check_output(command, shell=True)
        return output

    def clean_logcat(self):
        self.adb("adb logcat -c")

    # Send email summary with attachment
    def send_email(self, pass_fail):
        time.sleep(5)
        fromaddr = "MobileAutomationAlert@comscore.com"
        # This is what it will show in the TO: Field
        toaddr = "boo@comscore.com, mobile.comscore@gmail.com, MobileMeterQA@comscore.com"
        pwd = base64.b64decode(b"TTBiIUwzQXV0MCE=")
        pwd = pwd.decode("utf-8")
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = f"[{pass_fail}] Automation test report - " + self.folder_name
        body = "Attached is the automation test summary for - " + self.folder_name  + \
               ".\n" "All files related to this test can be found @ " + self.folder_path \
                + "\nOR\n" + self.shared_path + "\\" + "results" + self.folder_name \
                + " if you copied to shared drive in your script."
        msg.attach(MIMEText(body, 'plain'))
        filename = self.test_log
        # file_path = directory + "\\" + "Test_Document.txt"
        attachment = open(filename, "rb")
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.ehlo()
        server.starttls()
        server.login(fromaddr, pwd)
        text = msg.as_string()
        # 2nd parameter is the email address that will send to( Make sure it is the same as TO field but as a list
        server.sendmail("MobileAutomationAlert@comscore.com", ["boo@comscore.com", "mobile.comscore@gmail.com"], text)
        server.quit()

    # swype to unlock (Android 6 and up)
    def swipe_unlock(self):
        self.adb("adb shell input keyevent 82")

    # swipe to unlock KitKat (Android 6)
    def swipe_unlock_kk(self):
        self.adb("adb shell input swipe 750 2100 750 1400")

    # Wakeup the device
    def wake_up(self):
        self.adb("adb shell input keyevent KEYCODE_WAKEUP")

    # unlock with Pin
    def unlock_with_pin(self, pin):
        self.adbshell(f"adb shell input text {pin} && adb shell input keyevent 66")

    # tap Enter key
    def enter_key(self):
        self.adb("adb shell input keyevent 66")
		
	
	# This is to restart the adb again in the test after stopping it. Notmally adb will start at the beginning of the test. 
    def start_adb(self):
        proc = subprocess.Popen(["adb", "logcat", "-v", "threadtime"], stdout=self.to_adb, stderr=self.to_adb,
                            shell=False)
        return proc
		
	# This is for Huawei device to clear the file access permission pop up
    def allow_access(self):
        if self.check_if_present("Allow_Access", "resource-id", "com.android.settings:id/btn_yes"):
            self.tap_this("Allow_Access", "resource-id", "com.android.settings:id/btn_yes")

    # Call this to stop adb logging
    def stop_adb(self):
        pid = self.proc.pid
        self.proc.terminate()
        # Check if the process has really terminated & force kill if not.
        try:
            self.proc.kill()
            self.logthis.write("\ninit:: stopping adb.\n")
            print("Will stop the ADB logging now.\n")
        except OSError:
            self.logthis.write("\ninit:: adb terminated gracefully.\n")
            print("Terminated gracefully")

    # Check device is plugged in or not
    def check_device(self):
        term_d = "device"
        output = self.adb("adb devices")
        output = str(output, 'UTF-8')
        is_device_present = output.split()  # split the output to check device is in the output
        # Print device connected status
        if term_d in is_device_present:
            print("Device found!")
            self.logthis.write("check_device:: Device found!\n")
        else:
            print("Device is not attached!")
            self.logthis.write("check_device:: Device is not attached! Stopping the test\n")
            self.stop_adb()
            self.logthis.close()
            self.send_email("FAILED")
            exit()
	
	# Check if the VPN is connected or not on the test device and return True or False
    def is_VPN_Connected(self):
        try:
            output = self.adb("adb shell dumpsys connectivity | grep -i 'VPN ()'")
            output = str(output, 'UTF-8')
            print(f"output is {output}")
            if "VPN ()" in output:
                now = datetime.datetime.now()
                current_time = now.strftime("%m-%d-%y-%H-%M-%S")
                self.logthis.write(f"\nis_VPN_Connected:: {current_time} - VPN is connected!\n")
                return True
            else:
                now = datetime.datetime.now()
                current_time = now.strftime("%m-%d-%y-%H-%M-%S")
                self.logthis.write(f"\nis_VPN_Connected:: {current_time} - VPN is not connected!\n")
                print("I'm in the disconnected loop")
                return False
        except subprocess.CalledProcessError:
            now = datetime.datetime.now()
            current_time = now.strftime("%m-%d-%y-%H-%M-%S")
            self.logthis.write(f"\nis_VPN_Connected:: {current_time} - Exception:: VPN is not connected!\n")
            return False
	
	# this is to check the check box status (checked or unchecked) 
    def is_checked(self, page, attr, item):
        x = False
        root = self.get_xml(page)
        # Check the checked value
        for text in root.iter("node"):
            xml_dict = text.attrib
            if item in xml_dict[attr] and  xml_dict["checked"] == "true":
                print("is_checked:: " + item + " is checked.\n")
                self.logthis.write("is_checked:: " + item + " is checked\n")
                x = True
                break
        return x
		
	# To reboot the device 
    def reboot(self):
        self.adb("adb reboot")
        time.sleep(30)
        for x in range(5):
            y = 0
            # check device is connected or not
            term_d = "device"
            output = self.adb("adb devices")
            output = str(output, 'UTF-8')
            is_device_present = output.split()  # split the output to check device is in the output
            # Print device connected status
            if term_d in is_device_present:
                print("Device found!")
                break
            else:
                print("Device is not attached! waiting 10 more seconds ")
                y += 1
                self.adb("adb kill-server")
                self.adb("adb start-server")
                time.sleep(10)
            if y == 5:
                print("Device is taking too long to reboot!")
                self.stop_adb()
                self.logthis.close()
                self.send_email("FAILED")
                exit()
        time.sleep(30)

    # Push the .e file
    def push_file(self, file_name, destination):
        self.logthis.write(f"push_file:: pushing the {file_name} to {destination}\n")
        try:
            term_pushed = "[100%]"
            device_output = self.adb(f"adb push {file_name} {destination}")
            device_output = str(device_output, 'UTF-8')
            push_check = device_output.split()  # split the output to check device is in the output
            # Print device connected status
            if term_pushed in push_check:
                print(f"push_file:: {file_name} pushed successfully\n")
                self.logthis.write(f"push_file:: {file_name} pushed successfully\n")
            else:
                print(f"{file_name} push failed for some reason\n")
                self.logthis.write(f"push_file:: {file_name} push failed for some reason. Skipping to next step.\n")
        except NameError:
            self.logthis.write(f"push_file:: Exception occured while pushing {file_name} to {destination}. \n")
            self.stop_adb()
            self.logthis.close()
            self.send_email("FAILED")
            exit()

    # Check internet connection of the device 
    def check_connection(self):
        try:
            term_d = "from"
            # ping google
            device_output = self.adb("adb shell ping -c 3 www.yahoo.com")
            device_output = str(device_output, 'UTF-8')
            connection_check = device_output.split()  # split the output to check device is in the output
            # Print device connected status
            if term_d in connection_check:
                print("Network - OK!")
                self.logthis.write("check_connection:: Network connection on device - OK!\n")
            else:
                print("No Network connection! aborting test")
                self.logthis.write("check_connection:: No internet connection! Stopping test\n")
                self.stop_adb()
                self.logthis.close()
                self.send_email("FAILED")
                exit()
        except subprocess.CalledProcessError:
            self.logthis.write("check_connection:: Exception occured while checking network connection of the device.\n")
            self.stop_adb()
            self.logthis.close()
            self.send_email("FAILED")
            exit()
	
	# To clear the app date of the specific app 
    def clear_app_data(self, test_app):
        # print('Ignore the "Failed" or "Success" below this line. It is for clearing the app data.\n')
        clear_output = self.adb(f"adb shell pm clear {test_app}")
        if clear_output == 0:
            print("App data cleared!")
            self.logthis.write("clear_app_data:: App data cleared!\n")
        else:
            print("There is no app data to clear!")
            self.logthis.write("clear_app_data:: There is no app data to clear!")

    # Force Stop an app with package name
    def force_stop(self, app):
        self.adbshell(f"adb shell am force-stop {app}")
        print(f"Force stopping the {app}")
        self.logthis.write(f"force_stop:: Force stopping the {app}\n")
		
	# This is to get the xml file of the device screen
    def get_xml(self, page):
        # subprocess.call("adb devices", shell=False)
        y = 0
        x = 0
        #xml_file = ""
        while x == 0 and y < 10:
            term_check = "UI hierchary dumped to"
            term_check2 = "reset_reason_init"
            output = self.adb("adb shell uiautomator dump")
            output = str(output, 'UTF-8')
            # if app is not installed wait 10 seconds and check install status
            if term_check in output:
                x = 1
            elif term_check2 in output:
                x = 1
            else:
                self.adb("adb kill-server")
                time.sleep(2)
                self.adb("adb start-server")
                y += 1
                time.sleep(5)
        if y == 10:
            print(f"get_xml:: get_xml Could not get the {page}.xml file")
            self.logthis.write(f"get_xml:: Could not get the {page}.xml file after 10 tries.\n Reboot the device and try again.\n")
            self.screenshot_exit(page)
		# Copy the xml file from the device to the test folder
        os.chdir(self.folder_path)
        self.adb(f'adb pull /sdcard/window_dump.xml {page}.xml')
        self.adb(r'adb shell rm /sdcard/window_dump.xml')
        xml_file = os.path.join(self.folder_path, f"{page}.xml")
		# Parse the XML file
        tree = ET.parse(xml_file)
        # get the root of the xml file
        root = tree.getroot()
        return root

    # Take screenshot_exit and kill adb loggingd
    def screenshot_exit(self, item):
        self.adb("adb shell screencap /sdcard/screen.png")
        self.adb("adb pull /sdcard/screen.png screen.png")
        self.adb("adb shell rm /sdcard/screen.png")
        shutil.move("screen.png", self.folder_path + "\\" + time.strftime(
            "No_" + item + "_" + "%Y" + "-" + "%m" + "-" + "%d" + "-" + "%H" + "-" + "%M" + "-" + "%S.png"))
        self.logthis.write("screenshot_exit:: Some error occured, stopping the test after taking screenshot.\n")
        time.sleep(3)
        self.stop_adb()
        self.logthis.close()
        self.send_email("FAILED")
        exit()

	# Get the screenshot of the device 
    def screenshot_only(self, item):
        self.adb("adb shell screencap /sdcard/screen.png")
        self.adb("adb pull /sdcard/screen.png screen.png")
        self.adb("adb shell rm /sdcard/screen.png")
        shutil.move("screen.png", self.folder_path + "\\" + time.strftime(
            "No_" + item + "_" + "%Y" + "-" + "%m" + "-" + "%d" + "-" + "%H" + "-" + "%M" + "-" + "%S.png"))

    # This function is to verify that we are on correct page of the app or not
    def verify_page(self, page, attr, item):
        x = 0
        # Try 4 times (10s wait) for the page load
        for _ in range(4):
            # Get xml and get root
            root = self.get_xml(page)
            # Itirate to get the attribute of each nodes
            # Wait 10 seconds if page is not loaded
            for text in root.iter("node"):
                # This will create a dictionary for each nodes
                xml_dict = text.attrib
                if item in xml_dict[attr]:
                    print("verify_page:: " + item + " page loaded properly\n")
                    self.logthis.write("verify_page:: " + item + " page loaded properly\n")
                    return root
            x += 1
            y = str(10 * x)
            if x < 4:
                print(item + f" not found, waiting {y} seconds")
                time.sleep(10)
            if x == 4:
                self.logthis.write("verify_page:: " + item + " page is missing\n")
                print("verify_page:: " + item + " page is missing")
                self.screenshot_exit(item)

    # This function is to get the text from the page
    # Fail to get the text will not stop the test
    def get_text(self, root, attr, item):
        for text in root.iter("node"):
            # this will create a dictionary for each node
            xml_dict = text.attrib
            if item in xml_dict[attr]:
                my_text = (xml_dict['text'])
                #print(f"My Text is: {my_text}")
                my_text = my_text.rstrip()
                return my_text
        # If for loop didn't find it print the missing
        print(item + " is missing on the screen")
        self.logthis.write(f"get_text:: + {item} not found on the screen.\n")
        self.screenshot_only(item)
        return "TEXT_NOT_FOUND"

    # This function is to get the x and y of the button
    def get_xy(self, root, attr, item):
        # Itirate to get the attribute of each nodes
        xy_list = [0, 0]
        for tag in root.iter("node"):
            # this will create a dictionary for each node
            xml_dict = tag.attrib
            # print(x)
            # print(type(x))
            # Find a desire text in the dictionary's value, and then print the value of the key "bounds"
            if item in xml_dict[attr]:
                coords = xml_dict['bounds']
                # This will print the bounds
                # Below is to find the average of x and y in the bounds above
                comma_1 = coords.find(",")
                x_1 = coords[1:comma_1]
                # print(x_1)
                str_1 = coords[comma_1 + 1:]
                # print(str_1)
                bracket_2 = str_1.find(']')
                y_1 = str_1[:bracket_2]
                # print(y_1)
                str_2 = str_1[bracket_2 + 2:]
                # print(str_2)
                comma_2 = str_2.find(',')
                x_2 = str_2[:comma_2]
                # print(x_2)
                str_3 = str_2[comma_2 + 1:]
                # print(str_3)
                bracket_3 = str_3.find(']')
                y_2 = str_3[:bracket_3]
                # print(y_2)
                x: float = (int(x_1) + int(x_2)) / 2
                y = (int(y_1) + int(y_2)) / 2
                x = int(x)
                y = int(y)
                # Create a list and return the value of x and y in the list
                xy_list = [x, y]
                return xy_list

    # Scroll down a very little (small)
    def scroll_down_xs(self):
        x1 = 500
        y1 = 500
        x2 = 300
        y2 = 300
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # Scroll down a little (small)
    def scroll_down_s(self):
        x1 = 500
        y1 = 650
        x2 = 300
        y2 = 300
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # scroll down medium
    def scroll_down_m(self):
        x1 = 500
        y1 = 900
        x2 = 300
        y2 = 250
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # scroll down Large
    def scroll_down_l(self):
        x1 = 500
        y1 = 1200
        x2 = 300
        y2 = 300
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # Scroll down a little (small)
    def scroll_up_s(self):
        x1 = 300
        y1 = 300
        x2 = 500
        y2 = 650
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # scroll down medium
    def scroll_up_m(self):
        x1 = 300
        y1 = 300
        x2 = 500
        y2 = 1000
        x_axis = int(self.get_x())
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # scroll down large
    def scroll_up_l(self):
        x1 = 300
        y1 = 300
        x2 = 500
        y2 = 1200
        x_axis = int(self.get_x())
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        x1 = x1 * x_axis / 1080
        x2 = x2 * x_axis / 1080
        y1 = y1 * y_axis / 1920
        y2 = y2 * y_axis / 1920
        device_model = str(self.adb("adb devices -l"))
        if "SAMSUNG_SM_N910A" or "SM_G920T" in device_model:
            y1 = y1 + 120
            y2 = y2 + 120
        self.adb(f"adb shell input swipe {x1} {y1} {x2} {y2}")
        time.sleep(2)

    # hide keyboard
    def hide_keyboard(self):
        time.sleep(2)
        self.adb("adb shell input keyevent 111")
        time.sleep(1)

    # Tap Home button
    def tap_home(self):
        time.sleep(2)
        self.adb("adb shell input keyevent 3")
        time.sleep(2)

    # Tap on screen x y
    def tap(self, x, y):
        if x > 0 and y > 0:
            self.adb(f'adb shell input tap {x} {y}')
        time.sleep(2)

    # This function will tap whatever item in "this" you provided.
    # NOTE: This function will create an XML file every time you call this, so use it only if you just want to press one button on the page
    # If you have to verify multiple items on the same page, use get_xy() and tap(x,y) functions instead (it will speed up the test time)
    def tap_this(self, this, id, item):
        root = self.get_xml(this)
        if self.check_if_present_no_root(root, id, item):
            xy = self.get_xy(root, id, item)
            x = xy[0]
            y = xy[1]
            self.tap(x, y)
            # print(xy)
            print((f"tap_this:: Tapped the {item}\n"))
            self.logthis.write(f"tap_this:: Tapped the {item}\n")
        else:
            self.logthis.write(f"tap_this:: {item} is not on the page to tap.\n")
            self.screenshot_exit(item)
        return root
		
	# This is to tap somewhere without parsing the xml again 
    def tap_this_no_root(self, root, id, item):
        if self.check_if_present_no_root(root, id, item):
            xy = self.get_xy(root, id, item)
            x = xy[0]
            y = xy[1]
            self.tap(x, y)
            # print(xy)
            print((f"tap_this_no_root:: Tapped the {item}\n"))
            self.logthis.write(f"tap_this_no_root:: Tapped the {item}\n")
        else:
            self.logthis.write(f"tap_this_no_root:: {item} is not on the page to tap.\n")
            self.screenshot_exit(item)
			
    # Enter Text
    def enter_text(self, mytext):
        self.adb(f'adb shell input text {mytext}')
        time.sleep(2)
        self.logthis.write(f"enter_text:: Entered {mytext} \n")

    ##### For Huawei P9 device only ########
    # This will clear recent apps and bring up the Home screen.
    def homescreen(self):
        # create at least one recent app (Gmail)
        subprocess.call(
            f"adb shell am start -a android.intent.action.VIEW -d 'market://details?id=com.google.android.gm'",
            shell=False)
        # Tap Recent apps
        self.adb("adb shell input keyevent KEYCODE_APP_SWITCH")
        time.sleep(1)
        # Verify the page is recent apps
        self.verify_page("RecentApp", "resource-id", "clear_all_recents_image_button")
        # Get the x and y of the Clear All button
        self.tap_this("Recent", "resource-id", "clear_all_recents_image_button")
        # Tap Home
        self.tap_home()
        time.sleep(1)

    def allow_file_permission(self):
        self.tap_this("Allow_Permission", "resource-id", "permission_allow_button")

    def allow_phone_permission(self):
        self.tap_this("Allow_Permission", "resource-id", "permission_allow_button")

    # Get reference text from excel file
    def get_ref_text(self, translation_excel, key, language):
        # assign the reference excel file
        book = pe.get_book(file_name=translation_excel)
        # Set the sheet that has translations
        sheet = book.sheet_by_index(0)
        lookup = {
            "en-us": 1, "es-us": 2, "en-ca": 3, "fr-ca": 4, "en-gb": 5, "es-eu": 6
            , "es-mx": 7, "pt-br": 8, "it": 9, "de-de": 10, "fr-fr": 11, "ms-my": 12
            , "id-id": 13, "nb-no": 14}

        if language in lookup:
            col = lookup[language]
            for row in sheet:
                if row[0] == key:
                    # if "button_2" in row[0]:
                    # print("%s" % row[col])
                    text = row[col]
                    text = text.rstrip()
                    if text is None:
                        text = ""
                    return text
        else:
            self.logthis.write("get_ref_text:: Language passed in the function is not valid.")
            print(language + " is not the valid language id")
            return "KEY_NOT_FUND_IN_EXCEL"

    # This will verify the text with the reference
    # key is in the the text key from the first column of the excel file
    # language = en-us, ca-fr etc...
    # id and value are from xml file
    def get_XML_verify_text(self, translation_excel, key, language, attr, item):
        # get ref text
        ref = self.get_ref_text(translation_excel, key, language)
        root = self.get_xml(key)
        app_text = self.get_text(root, attr, item)
        # print(app_text)
        if ref != app_text:
            print(key + " text didn't match: FAILED")
            self.logthis.write("get_XML_verify_text:: Expected: " + ref + "\n")
            self.logthis.write("get_XML_verify_text:: Actual: " + app_text + "\n")
            # print(ref)
            # print(app_text)
        else:
            print(key + " text matched!")
            self.logthis.write(f"get_XML_verify_text:: {key} text macthed!\n")
        return root

    def verify_text_excel(self, root, translation_excel, key, language, attr, item):
        # get ref text
        ref = self.get_ref_text(translation_excel, key, language)
        app_text = self.get_text(root, attr, item)
        # print(app_text)
        if ref != app_text:
            print(key + " text didn't match: FAILED")
            self.logthis.write("verify_text:: Expected: " + ref + "\n")
            self.logthis.write("verify_text:: Actual: " + app_text + "\n")
            # print(ref)
            # print(app_text)
        else:
            print(key + " text matched!")
            self.logthis.write(f"verify_text:: {key} text macthed! PASSED\n")

    def verify_text_only(self, root, ref, attr, item):
        app_text = self.get_text(root, attr, item)
        # print(app_text)
        if ref not in app_text:
            print(ref + " text didn't match: FAILED")
            self.logthis.write("verify_text:: Expected: " + ref + "\n")
            self.logthis.write("verify_text:: Actual: " + app_text + "\n")
            # print(ref)
            # print(app_text)
        else:
            print(ref + " text matched!")
            self.logthis.write(f"verify_text:: {ref} text macthed! PASSED\n")


    # Kill and uninstall an app
    def uninstall(self, package_name):
        print(f"uninstall:: Uninstalling the {package_name}. Please ignore if you see the error!")
        # Kill MMS
        self.adb(f"adb uninstall {package_name}")
        self.logthis.write("uninstall:: " + package_name + " uninstalled successfully\n")
        time.sleep(2)

    # launch the app, app = package name
    def launch(self, app):
        self.adbshell(f"adb shell monkey -p {app} 1")
        print(f"{app} launched.")
        time.sleep(4)
        self.logthis.write(f"launch:: {app} Started.\n")

    def start_activity(self, activity):
        self.adbshell(f"adb shell am start -n {activity}")

    def launch_vpn_activity(self):
        self.adbshell(f"adb shell am start -n 'com.android.settings/com.android.settings.Settings^$VpnSettingsActivity'")

    # Use this to to sideload apk
    def sideload(self, package, apk):
        try:
            print(f"Uninstalling the {package}. You may see an error if the app is not installed. Ignore if you see the error! ")
            self.uninstall(package)
            time.sleep(5)
            output = self.adb(f"adb install {apk}")
            output = str(output, 'UTF-8')
            if "Success" in output:
                print(f"{package} installed successfully")
                self.logthis.write("sideload:: " + apk + " installed successfully\n")
            else:
                self.logthis.write(f"sideload:: {apk} install failed")
                print(f"Error occured during the installation of {apk}.")
                self.stop_adb()
                self.logthis.close()
                self.send_email("FAILED")
                exit()
        # Output the install error
        except NameError:
            self.logthis.write(f"sideload:: {apk} install failed")
            print(f"Error occured during the installation of {apk}.")
            self.stop_adb()
            self.logthis.close()
            self.send_email("FAILED")
            exit()
        time.sleep(15)

    # Use this to to sideload apk
    def sideload_only(self, package, apk):
        try:
            print(
                f"Installing the {package}. This will replace the app if app is already installed! ")
            self.logthis.write(f"sideload_only:: Installing the {apk} with replace option.\n")
            time.sleep(3)
            output = self.adb(f"adb install {apk}")
            output = str(output, 'UTF-8')
            if "Success" in output:
                print("APK Install Success")
                self.logthis.write("sideload:: " + apk + " installed successfully\n")
            else:
                self.logthis.write(f"sideload:: {apk} install failed")
                print(f"Error occured during the installation of {apk}.")
                self.stop_adb()
                self.logthis.close()
                self.send_email("FAILED")
                exit()
        # Output the install error
        except NameError:
            self.logthis.write(f"sideload_only:: {apk} install failed")
            print(f"Error occured during the installation of {apk}.")
            self.stop_adb()
            self.logthis.close()
            self.send_email("FAILED")
            exit()
        # time delay for slow devices
        time.sleep(10)

    # To get the app version installed on the device, pass the package name as parameter
    def get_app_version(self, package):
        x = 0
        for _ in range(4):
            term_package = package
            output = self.adb("adb shell pm list packages -f")
            output = str(output, 'UTF-8')
            # if app is not installed wait 10 seconds and check install status
            if term_package in output:
                print(f"Retrieved the test_app: {package}, information successfully!")
                app_version = self.adb(f"adb shell dumpsys package {package} | grep versionName")
                app_version = str(app_version, 'UTF-8')
                self.logthis.write(f"\n++++++++ TEST App Info +++++++++++\n")
                self.logthis.write(f"get_app_version:: The package name of the Test app installed is : {package}\n")
                self.logthis.write(f"\nget_app_version:: {package} Version: {app_version}")
                print(f"get_app_version:: {package} Version: {app_version}")
                target_SDK = subprocess.check_output(f"adb shell dumpsys package {package} | grep targetSdk",
                                                     shell=True)
                target_SDK = str(target_SDK, 'UTF-8')
                self.logthis.write(f"get_app_version:: {package} targeted SDK versions: {target_SDK}")
                self.logthis.write(f"++++++++ End of TEST App Info +++++++++++\n")
                break
            else:
                x += 1
                if x < 4:
                    print(f"Waiting for {str(x * 20)} seconds")
                    time.sleep(20)
        if x == 4:
            print(package + " is still not installed after 60 seconds")
            self.logthis.write(f"get_app_version:: {package} is still not installed after 60 seconds.\n")

    def edit_url(self, x, y, url):
        self.adb(f"adb shell input swipe {x} {y} {x} {y} 2000")
        time.sleep(2)
        # Enter Spoofing IP
        self.adb(f'adb shell input text {url}')
        time.sleep(1)
        self.hide_keyboard()
        time.sleep(2)

    # Check if the page is present
    def check_if_present(self, page, attr, item):
        x = False
        root = self.get_xml(page)
        # Check the page is there or not
        for text in root.iter("node"):
            # This will create a dictionary for each nodes
            xml_dict = text.attrib
            if item in xml_dict[attr]:
                print("check_if_present:: " + item + " is present.\n")
                self.logthis.write("check_if_present:: " + item + " is present\n")
                x = True
                break
        return x
	
	# This will scroll to that object if it is not visible yet
    def scroll_to_view(self, page, attr, item):
        x = False
        count = 1
        for _ in range(10):
            if count < 11 and x == False:
                x = self.check_if_present(page, attr, item)
                if x == False:
                    self.scroll_down_m()
                    count = count + 1
                else:
                    self.scroll_down_xs()
                    break

    # Reset application (clear dev cache)
    def clear_devcache(self, meterconfig):
        x = 0
        self.launch(meterconfig)
        time.sleep(1)
        # Verify Meterconfig app is loaded
        while self.check_if_present("Reset_Button", "resource-id", "com.example.dporter.meterconfig:id/updateButton") == False and x < 3:
            self.scroll_down_s()
            x += 1
        self.tap_this("Reset_Button", "resource-id", "com.example.dporter.meterconfig:id/resetRegistration")
        self.tap_home()

    # This is to check if anything is visible in webview or chrome (special case)
    # It required the itrm itself and reference item to compare
    # if coordinates of both items are the same, it is hidden and not visible
    # Use in the ula_en_us for ACCEPT and DECLINE buttons
    def check_if_visible(self, attrib_01, value_01, attrib_02, value_02):
        root = self.get_xml("Visible_or_not")
        list_1 = self.get_xy(root, attrib_01, value_01)
        list_2 = self.get_xy(root, attrib_02, value_02)
        self.adb(f"adb shell input swipe 500 430 650 300")
        if list_1 == list_2:
            return False
        else:
            return True

    # This function will install and set up meterconfig app to run test in TEST
    def setup_meterconfig_test(self, meterconfig_apk, meterconfig):
        self.sideload(meterconfig, meterconfig_apk)
        # Clean up home screen
        self.homescreen()
        # Launch MeterConfig
        self.launch(meterconfig)
        time.sleep(1)
        # Verify Meterconfig app is loaded
        self.verify_page("MeterConfig", "text", "Meter Configuration Tool")
        # Get the x and y of Reset Application
        root = self.get_xml("MeterConfig_01")
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/resetRegistration")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # sleep 4 additional minutes, reset need more time
        time.sleep(4)
        # Load Testing defaults
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/defaultsButton")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 1
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ciCertDLUrlOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 2
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ciPPAcceptUrlOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 3
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/webServerOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 4
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/regUrlOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 5
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/postFreqMinOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 6
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/postRetryMinOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Enable Use device storage for csproxy configuration FOR LTVPN
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ltvpnUseExtern")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Tap and hold REG url
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ltvpnUseExtern")
        x = xy[0]
        y = xy[1]
        self.edit_url(x, y, "http://test.mobilexpression.com/meterconfirmphone.aspx")
        # Scroll Down
        self.scroll_down_m()
        # Get XML again after scroll down
        root = self.get_xml("MeterConfig_02")
        # Enable All Logger
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/allLoggersButton")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Tap Update
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/updateButton")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Tap home
        self.tap_home()

    # Call this meterconfig function for PROD install
    def setup_meterconfig_prod(self, meterconfig, meterconfig_apk):
        self.sideload(meterconfig, meterconfig_apk)
        # Clean up home screen
        self.homescreen()
        # Launch MeterConfig
        self.launch(meterconfig)
        time.sleep(1)
        # Verify Meterconfig app is loaded
        self.verify_page("MeterConfig", "text", "Meter Configuration Tool")
        # Get the x and y of Reset Application
        root = self.get_xml("MeterConfig_01")
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/resetRegistration")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # sleep 4 additional minutes, reset need more time
        time.sleep(4)
        # Load Testing defaults
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/defaultsButton")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 1
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ciCertDLUrlOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 2
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ciPPAcceptUrlOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 3
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/webServerOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 4
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/regUrlOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 5
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/postFreqMinOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # tick checkbox 6
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/postRetryMinOvr")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Enable Use device storage for csproxy configuration FOR LTVPN
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ltvpnUseExtern")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Tap and hold REG url
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/ltvpnUseExtern")
        x = xy[0]
        y = xy[1]
        self.edit_url(x, y, "http://www.mobilexpression.com/meterconfirmphone.aspx")
        # Scroll Down
        self.scroll_down_m()
        # Get XML again after scroll down
        root = self.get_xml("MeterConfig_02")
        # Enable All Logger
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/allLoggersButton")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Tap Update
        xy = self.get_xy(root, "resource-id", "com.example.dporter.meterconfig:id/updateButton")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Tap home
        self.tap_home()

    # This function check the activity in the foreground
    # I rarely use this function
    # and uninstall MMS app if the verification failed
    # example page: Begin
    # example activity: mms.ui.activities.MainActivity
    def check_activity(self, page, activity):
        term_activity = activity
        output = self.adb("adb shell dumpsys window windows | grep -E mCurrentFocus")
        output = str(output, 'UTF-8')
        if term_activity in output:
            print(page + " is loaded properly!\n")
            self.logthis.write(f"check_activity:: {page} loaded properly!\n")
        else:
            print(page + " is not in the foreground!\n")
            self.logthis.write(f"check_activity:: {activity} page is missing.\n")
            print(activity + " page is missing")
            self.screenshot_exit(activity)

    # ULA page with 3 check boxes
    # I'm not using "Tap_this()" function in this page for performance
    # This function can be re-write with new functions to verify text. Leave it as it for now
    def ula_en_us_old(self, translation_excel):
        self.verify_page("ULA", "text", "This software, provided")
        # Get XML
        root = self.get_xml("ULA")
        # Verify ULA text which will also verify ULA page is currently in the foregorud
        ula_text = self.get_ref_text(translation_excel, "ULA_Body", "en-us")
        ula_from_app = self.get_text(root, "text", "This software, provided")
        # Do verification logic here, print it for now
        if ula_text != ula_from_app:
            self.logthis.write("ULA body text doesn't match\n")
            self.logthis.write(f"Expected: {ula_text}\n")
            self.logthis.write(f"Actual: {ula_from_app}\n")
            print("ULA Body - NOT OK!")
        else:
            self.logthis.write("ULA body text- PASSED!\n")
            print("ULA Body - OK!")
        # Verify check box 1 text
        chk_1_ula_text = self.get_ref_text(translation_excel, "1st_Checkbox", "en-us")
        chk_1_ula_app = self.get_text(root, "resource-id", "cbAuthorized")
        # Do verification here, print it for now
        if chk_1_ula_text != chk_1_ula_app:
            self.logthis.write("Checkbox 1 text doesn't match\n")
            self.logthis.write("Expected: " + chk_1_ula_text + "\n")
            self.logthis.write("Actual: " + chk_1_ula_app + "\n")
            print("Checkbox 1 NOT OK!")
        else:
            self.logthis.write("Checkbox 1  matched. PASSED\n")
            print("Checkbox 1 = OK!")
        # Verify check box 2 text
        chk_2_ula_text = self.get_ref_text(translation_excel, "2nd_Checkbox", "en-us")
        chk_2_ula_app = self.get_text(root, "resource-id", "cbPPTOS")
        # Do verification here, print it for now
        if chk_2_ula_text != chk_2_ula_app:
            self.logthis.write("Checkbox 2 text doesn't match\n")
            self.logthis.write(f"Expected: {chk_2_ula_text}\n")
            self.logthis.write(f"Actual: {chk_2_ula_app} \n")
            print("Checkbox 2 NOT OK!")
        else:
            self.logthis.write("Checkbox 2  matched.\n")
            print("Checkbox 2 = OK!")
        # Verify check box 3 text
        chk_3_ula_text = self.get_ref_text(translation_excel, "3rd_Checkbox", "en-us")
        chk_3_ula_app = self.get_text(root, "resource-id", "cbSurvey")
        # Do verification here, print it for now
        if chk_3_ula_text != chk_3_ula_app:
            self.logthis.write("Checkbox 3 doesn't match\n")
            self.logthis.write("Expected: " + chk_3_ula_app + "\n")
            self.logthis.write("Actual: " + chk_3_ula_app + "\n")
            print("Checkbox 3 NOT OK!")
        else:
            self.logthis.write("Checkbox 3  matched.\n")
            print("Checkbox 3 = OK!")
        # Check checkbox 1
        xy = self.get_xy(root, "resource-id", "cbAuthorized")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # checkbox 2
        xy = self.get_xy(root, "resource-id", "cbPPTOS")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # checkbox 3
        xy = self.get_xy(root, "resource-id", "cbSurvey")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)
        # Get XML again after checking 3 check boxes to enable I Accept button
        root = self.get_xml("ULA")
        # Verify I accept text
        button_1 = self.get_ref_text(translation_excel, "Accept", "en-us")
        button_1_app = self.get_text(root, "resource-id", "accept")
        if button_1 != button_1_app:
            self.logthis.write("Button 1 text doesn't match\n")
            self.logthis.write(f"Expected: {button_1} \n")
            self.logthis.write(f"Actual: {button_1_app} \n")
            print("Accept button NOT OK!")
        else:
            self.logthis.write("Accept button text  matched. - PASSED\n")
            print("Accept button = OK!")
        # Verify I decline text
        button_2 = self.get_ref_text(translation_excel, "Decline", "en-us")
        button_2_app = self.get_text(root, "resource-id", "decline")
        if button_2 != button_2_app:
            self.logthis.write("Decline button text doesn't match\n")
            self.logthis.write(f"Expected: {button_2} \n")
            self.logthis.write(f"Actual: {button_2_app} \n")
            print("Decline button NOT OK!")
        else:
            self.logthis.write("Decline button text matched. - PASSED\n")
            print("Decline button = OK!")
        # Verify PP and TOS link text at the bottom
        pp_tos = self.get_ref_text(translation_excel, "PP_TOS_Link_Text", "en-us")
        pp_tos_app = self.get_text(root, "resource-id", "privacyLink")
        if pp_tos != pp_tos_app:
            self.logthis.write("PP and TOS text doesn't match\n")
            self.logthis.write(f"Expected: {pp_tos} \n")
            self.logthis.write(f"Actual: {pp_tos_app} \n")
            print("PP and TOS text NOT OK!")
        else:
            self.logthis.write("PP and TOS text matched. - PASSED\n")
            print("PP and TOS text = PASSED")
        # Tap I accept
        xy = self.get_xy(root, "resource-id", "accept")
        x = xy[0]
        y = xy[1]
        self.tap(x, y)

    def ula_en_us(self, translation_excel):
        # Get XML
        x = 0
        root = self.verify_page("ULA", "text", "MobileXpression is part of")
        # Consent check box text verification
        self.verify_text_excel(root, translation_excel, "consent_01", "en-us", "resource-id", "aboutMX")
        self.verify_text_excel(root, translation_excel, "consent_02", "en-us", "resource-id", "cbAuthorized")
        time.sleep(1)
        # Check the consent check box
        self.tap_this_no_root(root, "resource-id", "cbAuthorized")
        time.sleep(1)
        # Scroll down for small screen devices
        while self.check_if_visible("resource-id", "accept", "resource-id", "decline") == False and x < 4:
            self.scroll_down_m()
            x += 1
        self.tap_this("I_accept", "resource-id", "accept")

    def ula_native_en_us(self,translation_excel):
        root = self.verify_page("ULA", "text", "Privacy Policy and Terms of Service")
        self.verify_text_excel(root, translation_excel, "consent_01", "en-us", "resource-id", "tv_header")
        self.verify_text_excel(root, translation_excel, "consent_02", "en-us", "resource-id", "tv_accept")
        self.verify_text_excel(root, translation_excel, "consent_04", "en-us", "resource-id", "tv_footer")
        self.verify_text_excel(root, translation_excel, "consent_06", "en-us", "resource-id", "btn_left")
        self.verify_text_excel(root, translation_excel, "consent_05", "en-us", "resource-id", "btn_right")
        self.tap_this_no_root(root, "resource-id", "cb_accept")
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "btn_right")
        time.sleep(2)

    # This function will fill out US English Demo
    # Fill out US-EN Demos
    def demo_en_us(self, translation_excel, email):
        # get root
        time.sleep(4)
        root = self.get_xml("Demo_1")
        # Verify Text will also verify demo page is loaded
        mx_header_text_ref = self.get_ref_text(translation_excel, "demo_header", "en-us")
        mx_header_text_app = self.get_text(root, "text", "Create your MobileXpression account")
        if mx_header_text_app == mx_header_text_ref:
            self.logthis.write(f"Header text, {mx_header_text_app} found. - PASSED\n")
        # tap Email field
        # email_text_app = self.get_text(root, "text", "Email *")
        # print(email_text_app)
        self.tap_this_no_root(root, "resource-id", "panelist~v_username")
        # self.tap(550, 425)
        # Enter email
        self.adb(f'adb shell input text {email}')
        # Hide keyboard
        self.hide_keyboard()
        # Tap Age Questions
        self.tap_this_no_root(root, "resource-id", "house_member~0~age")
        # self.tap(250, 650)
        # Scroll down m two times
        self.scroll_down_m()
        time.sleep(2)
        self.scroll_down_m()
        time.sleep(2)
        self.scroll_down_m()
        time.sleep(2)
        # Select Age
        # root = self.get_xml("Age_dropdown")
        # self.tap_this("22", "text", "22")
        self.tap_xy(550, 1200)
        # root = self.get_xml("Gender")
        # Tap Gender
        time.sleep(3)
        self.tap_this_no_root(root, "resource-id", "house_member~0~c_gender")
        # self.tap(550, 850)
        # Select Gender
        time.sleep(2)
        # self.tap_this("Male", "text", "Male")
        self.tap_xy(450, 850)
        # Tap HH Income
        # root = self.get_xml("HH_Income")
        time.sleep(3)
        self.tap_this_no_root(root, "resource-id", "household_demo~6002")
        # self.tap(550, 1050)
        # Select HH Income
        time.sleep(3)
        # self.tap_this("40000-49999", "index", "5")
        self.tap_xy(550, 850)
        # Scroll down
        self.scroll_down_s()
        # Tap Zipcode
        # root = self.get_xml("ZipCode")
        time.sleep(4)
        root = self.get_xml("Demo_2")
        self.tap_this_no_root(root, "resource-id", "panelist~v_zip")
        # self.tap(550, 775)
        # Enter zip
        self.enter_text('20222')
        # Hide Keyboard
        self.hide_keyboard()
        time.sleep(3)
        self.tap_this_no_root(root, "resource-id", "panelist~i_num_members")
        # self.tap(550, 1000)
        # Select HH Size = 3
        # root = self.get_xml("HH-Size_Dropdown")
        time.sleep(2)
        # self.tap_this("HH-Size-A", "index", "3")
        self.tap_xy(550, 850)
        # Scroll down
        self.scroll_down_s()
        # Tap Children under 18
        time.sleep(4)
        root = self.get_xml("Demo_3")
        time.sleep(3)
        self.tap_this_no_root(root, "resource-id", "household_demo~6001")
        # self.tap(550, 750)
        # Select Children under 18 = yes
        time.sleep(2)
        # self.tap_this("Under_18-A", "index", "1")
        self.tap_xy(550, 850)
        # Tap Race
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6010")
        # self.tap(550, 950)
        # Select race
        # root = self.get_xml("Race_dropdown")
        time.sleep(2)
        # self.tap_this("Race-A", "index", "3")
        self.tap_xy(550, 850)
        # Scroll down
        self.scroll_down_m()
        # Tap Spanish Descent Question
        time.sleep(3)
        root = self.get_xml("Demo_4")
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6012")
        # Select Spanish Descent = Yes
        time.sleep(2)
        # self.tap_this("Spanish_Decent-A", "text", "Yes")
        self.tap_xy(550, 850)
        # Tap Spanish language question 1
        # root = self.get_xml("Spanish_Q_01")
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6020")
        # self.tap(550, 950)
        # Select Spanish 1 = Equally
        # root = self.get_xml("Spanish_Q_01_dropdown")
        time.sleep(2)
        # self.tap_this("Language_01-A", "index", "3")
        self.tap_xy(550, 850)
        # Tap Spanish language question 2
        # root = self.get_xml("Spanish_Q_02")
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6021")
        # self.tap(550, 1060)
        # Select Spanish 2 = Equally
        # root = self.get_xml("Spanish_Q_02_dropdown")
        time.sleep(2)
        # self.tap_this("Language_02-A", "index", "3")
        self.tap_xy(550, 850)
        # Tap Submit
        # root = self.get_xml("Submit")
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "submit")
        # tap(550, 1385)
        self.logthis.write("Demo completed!\n")

	# Demo on asus device
    def demo_en_us_asus(self, translation_excel, email):
        # get root
        time.sleep(4)
        root = self.get_xml("Demo_1")
        # Verify Text will also verify demo page is loaded
        mx_header_text_ref = self.get_ref_text(translation_excel, "demo_header", "en-us")
        mx_header_text_app = self.get_text(root, "text", "Create your MobileXpression account")
        if mx_header_text_app == mx_header_text_ref:
            self.logthis.write(f"Header text, {mx_header_text_app} found. - PASSED\n")
        # tap Email field
        # email_text_app = self.get_text(root, "text", "Email *")
        # print(email_text_app)
        self.tap_this_no_root(root, "resource-id", "panelist~v_username")
        # self.tap(550, 425)
        # Enter email
        self.adb(f'adb shell input text {email}')
        # Hide keyboard
        self.hide_keyboard()
        # Tap Age Questions
        self.tap_this_no_root(root, "resource-id", "house_member~0~age")
        # self.tap(250, 650)
        # Scroll down m two times
        self.scroll_down_m()
        time.sleep(2)
        self.scroll_down_m()
        time.sleep(2)
        self.scroll_down_l()
        time.sleep(2)
        # Select Age
        self.tap_xy(550, 1200)
        time.sleep(2)
        self.scroll_down_s()
        # Tap Gender
        root = self.get_xml("Demo_2")
        self.tap_this_no_root(root, "resource-id", "house_member~0~c_gender")
        # Select Gender
        time.sleep(2)
        self.tap_xy(450, 850)
        # Tap HH Income
        # root = self.get_xml("HH_Income")
        time.sleep(3)
        self.tap_this_no_root(root, "resource-id", "household_demo~6002")
        # Select HH Income
        time.sleep(3)
        self.tap_xy(550, 850)
        # Scroll down
        self.scroll_down_s()
        # Tap Zipcode
        time.sleep(3)
        root = self.get_xml("Demo_3")
        self.tap_this_no_root(root, "resource-id", "panelist~v_zip")
        # Enter zip
        self.enter_text('20222')
        # Hide Keyboard
        self.hide_keyboard()
        time.sleep(3)
        # Tap HH Size
        self.tap_this_no_root(root, "resource-id", "panelist~i_num_members")
        # Select HH Size = 3
        time.sleep(2)
        self.tap_xy(550, 850)
        # Scroll down
        self.scroll_down_s()
        time.sleep(2)
        self.scroll_down_xs()
        # Tap Children under 18
        time.sleep(4)
        root = self.get_xml("Demo_4")
        time.sleep(3)
        self.tap_this_no_root(root, "resource-id", "household_demo~6001")
        # Select Children under 18 = yes
        time.sleep(2)
        self.tap_xy(550, 850)
        # Tap Race
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6010")
        # Select race
        time.sleep(2)
        self.tap_xy(550, 850)
        time.sleep(2)
        # Tap Spanish Descent Question
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6012")
        # Select Spanish Descent = Yes
        time.sleep(2)
        self.tap_xy(550, 850)
        time.sleep(2)
        # Scroll down
        self.scroll_down_s()
        time.sleep(1)
        self.scroll_down_s()
        time.sleep(2)
        root = self.get_xml("Demo_5")
        # Tap Spanish language question 1
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6020")
        # Select Spanish 1 = Equally
        time.sleep(2)
        self.tap_xy(550, 850)
        # Tap Spanish language question 2
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "member_demo~0~6021")
        # Select Spanish 2 = Equally
        time.sleep(2)
        self.tap_xy(550, 850)
        # Tap Submit
        time.sleep(2)
        self.tap_this_no_root(root, "resource-id", "submit")
        self.logthis.write("Demo completed!\n")
		
	# Demo for native sdk	
    def demo_native_en_us(self, translation_excel, email):
        root = self.verify_page("Please_help_us", "resource-id", "tv_quest_prompt")
        # Tap next
        self.tap_this_no_root(root, "resource-id", "btn_right")
        # Enter email
        root = self.verify_page("Email_page", "resource-id", "et_answer")
        self.verify_text_only(root, "Email", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "et_answer")
        self.enter_text(email)
        self.enter_key()
        # Enter Age
        root = self.verify_page("Age", "resource-id", "tv_question")
        self.verify_text_only(root, "Age", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "et_answer")
        self.enter_text("23")
        self.enter_key()
        # Gender
        root = self.verify_page("Gender", "resource-id", "tv_question")
        self.verify_text_only(root, "Gender", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Male")
        # Annual household income
        root = self.verify_page("HH_Income", "resource-id", "tv_question")
        self.verify_text_only(root, "Annual household income", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "tv_answer")
        # zip code
        root = self.verify_page("Zip_code", "resource-id", "tv_question")
        self.verify_text_only(root, "Zip code", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "et_answer")
        self.enter_text("20113")
        self.enter_key()
        # Household size
        root = self.verify_page("Zip_code", "resource-id", "tv_question")
        self.verify_text_only(root, "Household size", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "5")
        # Children under 18
        root = self.verify_page("Under_18", "resource-id", "tv_question")
        self.verify_text_only(root, "Children under 18", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Yes")
        # Race
        root = self.verify_page("Under_18", "resource-id", "tv_question")
        self.verify_text_only(root, "Race", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "American Indian/Native Alaskan")
        # Spanish Descent
        root = self.verify_page("Spanish_01", "resource-id", "tv_question")
        self.verify_text_only(root, "Is anyone in", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Yes")
        # Spanish language 01
        root = self.verify_page("Spanish_01", "resource-id", "tv_question")
        self.verify_text_only(root, "Language you use", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Mostly English")
        # Spanish language 02
        root = self.verify_page("Spanish_02", "resource-id", "tv_question")
        self.verify_text_only(root, "Language you prefer", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Usually English")
        # Final Step
        root = self.verify_page("Spanish_02", "resource-id", "tv_rp_header")
        self.verify_text_only(root, "To enjoy the full benefits of the MobileXpression", "resource-id", "tv_rp_details")
        self.verify_text_only(root, "Cancel", "resource-id", "btn_fs_cancel")
        self.tap_this_no_root(root, "resource-id", "btn_fs_next")

    def demo_native_en_us_10_minutes(self, translation_excel, email):
        root = self.verify_page("Please_help_us", "resource-id", "tv_quest_prompt")
        # Tap next
        self.tap_this_no_root(root, "resource-id", "btn_right")
        time.sleep(2)
        # Enter email
        root = self.verify_page("Email_page", "resource-id", "et_answer")
        self.verify_text_only(root, "Email", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "et_answer")
        self.enter_text(email)
        self.enter_key()
        time.sleep(2)
        # Enter Age
        root = self.verify_page("Age", "resource-id", "tv_question")
        self.verify_text_only(root, "Age", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "et_answer")
        self.enter_text("23")
        self.enter_key()
        time.sleep(2)
        # Gender
        root = self.verify_page("Gender", "resource-id", "tv_question")
        self.verify_text_only(root, "Gender", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Male")
        time.sleep(2)
        # Annual household income
        root = self.verify_page("HH_Income", "resource-id", "tv_question")
        self.verify_text_only(root, "Annual household income", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "tv_answer")
        time.sleep(2)
        # zip code
        root = self.verify_page("Zip_code", "resource-id", "tv_question")
        self.verify_text_only(root, "Zip code", "resource-id", "tv_question")
        self.tap_this_no_root(root, "resource-id", "et_answer")
        self.enter_text("20113")
        self.enter_key()
        time.sleep(2)
        # Household size
        root = self.verify_page("Zip_code", "resource-id", "tv_question")
        self.verify_text_only(root, "Household size", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "5")
        time.sleep(2)
        # Children under 18
        root = self.verify_page("Under_18", "resource-id", "tv_question")
        self.verify_text_only(root, "Children under 18", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Yes")
        time.sleep(2)
        # Race
        root = self.verify_page("Under_18", "resource-id", "tv_question")
        self.verify_text_only(root, "Race", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "American Indian/Native Alaskan")
        time.sleep(2)
        # Spanish Descent
        root = self.verify_page("Spanish_01", "resource-id", "tv_question")
        self.verify_text_only(root, "Is anyone in", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Yes")
        time.sleep(2)
        # Spanish language 01
        root = self.verify_page("Spanish_01", "resource-id", "tv_question")
        self.verify_text_only(root, "Language you use", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Mostly English")
        time.sleep(2)
        # Spanish language 02
        root = self.verify_page("Spanish_02", "resource-id", "tv_question")
        self.verify_text_only(root, "Language you prefer", "resource-id", "tv_question")
        self.tap_this_no_root(root, "text", "Usually English")
        time.sleep(2)
        # Final Step
        root = self.verify_page("Spanish_02", "resource-id", "tv_rp_header")
        self.verify_text_only(root, "To enjoy the full benefits of the MobileXpression", "resource-id", "tv_rp_details")
        self.verify_text_only(root, "Cancel", "resource-id", "btn_fs_cancel")
        self.tap_this_no_root(root, "resource-id", "btn_fs_next")
        time.sleep(2)

    # This function will fill out US English Demo
    # Fill out US-EN Demos
    def demo_en_us_old(self, translation_excel, email):
        # get root
        root = self.get_xml("Demo")
        # Verify Text will also verify demo page is loaded
        # Verify Text will also verify demo page is loaded
        mx_header_text_ref = self.get_ref_text(translation_excel, "demo_header", "en-us")
        mx_header_text_app = self.get_text(root, "text", "Create your MobileXpression account")
        if mx_header_text_app == mx_header_text_ref:
            self.logthis.write(f"Header text, {mx_header_text_app} found. - PASSED\n")
        # Tap Email field
        self.tap_xy(500, 425)
        # Enter email
        self.enter_text(email)
        # Hide keyboard
        self.hide_keyboard()
        # Tap Age Questions
        self.tap_xy(550, 650)
        # Scroll down m two times
        self.scroll_down_m()
        self.scroll_down_m()
        # Select Age
        self.tap_xy(550, 1500)
        # Tap Gender
        self.tap_xy(550, 850)
        # Select Gender
        self.tap_xy(450, 850)
        # Tap HH Income
        self.tap_xy(550, 1050)
        # Select HH Income
        self.tap_xy(550, 1000)
        # Scroll down
        self.scroll_down_s()
        # Tap Zipcode
        self.tap_xy(550, 775)
        # Enter zip
        self.enter_text('20222')
        # Hide Keyboard
        self.hide_keyboard()
        # Tap HH Size
        self.tap_xy(550, 1000)
        # Select HH Size = 3
        self.tap_xy(550, 800)
        # Scroll down
        self.scroll_down_s()
        # Tap Children under 18
        self.tap_xy(550, 750)
        # Select Children under 18 = yes
        self.tap_xy(550, 800)
        # Tap Race
        self.tap_xy(550, 950)
        # Select race = American Indian
        self.tap_xy(550, 900)
        # Scroll down
        self.scroll_down_m()
        # Tap Spanish Descent
        self.tap_xy(550, 600)
        # Select Spanish Descent = Yes
        self.tap_xy(550, 850)
        # Tap Spanish 1
        self.tap_xy(550, 950)
        # Select Spanish 1 = Equally
        self.tap_xy(550, 950)
        # Tap Spanish 2
        self.tap_xy(550, 1060)
        # Select Spanish 2 = Equally
        self.tap_xy(550, 950)
        # Tap Submit
        self.tap_xy(550, 1385)
        #tap_this("Submit", "resource-id", "submit")
        # tap(550, 1385)
        print("Demo completed!")

    # This function is to check app is installed or not after 30 seconds
    # useful if the test is installing from Play Store and can not guess how long it take to complete the install
    def install_playstore(self, package):
        self.uninstall(package)
        self.adb(f"adb shell am start -a android.intent.action.VIEW -d 'market://details?id={package}'")
        time.sleep(10)
        # Check app page is loaded (This check is not pefrect but it is the best way for now)
        root = self.verify_page(package, "package", "com.android.vending")
        # Verify Text
        button_text = self.get_text(root, "class", "android.widget.Button")
        if button_text == "INSTALL":
            xy = self.get_xy(root, "class", "android.widget.Button")
            x = xy[0]
            y = xy[1]
            self.tap(x, y)
            self.logthis.write(f"install_playstore:: Installing {package} from Google Play Store.\n")
            if self.check_if_present("Accept", "text", "ACCEPT"):
                self.tap_this("Accept", "text", "ACCEPT")

    # This will check the app is installed on the device or not
    def check_installed_60s(self, app_name, package, apk):
        x = 0
        for _ in range(4):
            term_package = package
            output = self.adb("adb shell pm list packages -f")
            output = str(output, 'UTF-8')
            # if app is not installed wait 10 seconds and check install status
            if term_package in output:
                print("App is installed")
                self.logthis.write(f"check_installed_60s:: {app_name} is installed\n")
                break
            else:
                x += 1
                if x < 4:
                    print(f"{app_name} is not installed yet. Waiting for {str(x * 20)} seconds")
                    time.sleep(20)
        if x == 4:
            print(app_name + " is still not installed after 60 seconds")
            self.logthis.write(f"check_installed_60s:: Installtion of {app_name} from play store failed. Taking screenshot and sideload the app\n")
            self.screenshot_only(app_name)
            self.sideload(package, apk)

    # This will query to TEST db and return the i_installed flag as a result
    def sql_i_installed_test(self, email):
        connection = pypyodbc.connect('Driver={SQL Server};'
                                      'Server=csiadosd02;'
                                      'Database=csvadb2;'
                                      'uid=cswebid;pwd=comscore')
        cursor = connection.cursor()
        # SQLCommand = ("SELECT TOP 100* "
        #            "FROM dbo.mobile_sdk_user_session "
        #           "ORDER BY dt_create DESC")
        SQLCommand = (
            f"select i_installed from mobile_tracking (nolock) where v_signup_email = '{email}'")
        cursor.execute(SQLCommand)
        results = cursor.fetchone()
        return results

    # This function will get bid from db
    def get_bid_db_test(self, email):
        connection = pypyodbc.connect('Driver={SQL Server};'
                                      'Server=csiadosd02;'
                                      'Database=csvadb2;'
                                      'uid=cswebid;pwd=comscore')
        cursor = connection.cursor()
        # SQLCommand = ("SELECT TOP 100* "
        #            "FROM dbo.mobile_sdk_user_session "
        #           "ORDER BY dt_create DESC")
        SQLCommand = (
            f"select c_installed_machine_id from mobile_tracking (nolock) where v_signup_email = '{email}' order by dt_create desc")
        cursor.execute(SQLCommand)
        results = cursor.fetchone()
        bid = results[0]
        self.logthis.write(f"\nget_bid_db_test:: BID is {bid}\n")
        return bid

    # This function will get bid from adb logs
    def get_bid_from_adb(self, adb_log):
        bid = "00000000"
        with open(adb_log, 'r', errors='ignore') as log:
            for text in log:
                str_index = (text.find('metercheck.aspx?id='))
                if str_index > 0:
                    bid = (text[str_index + 19: str_index + 41])
                    self.logthis.write(f"\nget_bid_from_adb:: BID is {bid}\n")
            return bid

    def get_netforward_version(self, adb_log):
        nf_version = ""
        with open(adb_log, 'r', errors='ignore') as log:
            for text in log:
                str_index_1 = (text.find('NetForward.Service: setConfig()'))
                if str_index_1 > 0:
                    nf_version = (text[str_index_1 + 31: str_index_1 + 61])
                    self.logthis.write(f"\nget_netforward_version:: Netforward version is {nf_version}\n")
            return nf_version

    # Create the split bid
    def split_bid(self, bid):
        split_bid = "x-ns1" + bid[0:11] + ",x-ns2" + bid[11:]
        return split_bid

    def launch_install(self):
        # Verify launch install page is loaded by checking the "Next" button present
        self.verify_page("launch_install", "resource-id", "submitButton")
        # Can't verify text yet, need resource-id value
        # get_XML_verify_text("Launch_install_body_text_01", "en-ud", "text", "" )
        self.tap_this("Next", "resource-id", "submitButton")
        self.logthis.write("launch_install:: Tapped the Next button\n")

    def launch_install_native(self):
        # Verify launch install page is loaded by checking the "Next" button present
        self.verify_page("launch_install", "resource-id", "tv_rp_details")
        # Can't verify text yet, need resource-id value
        # get_XML_verify_text("Launch_install_body_text_01", "en-ud", "text", "" )
        self.tap_this("Next", "resource-id", "btn_fs_next")
        self.logthis.write("launch_install:: Tapped the Next button\n")

    # Verify Enable Accessibility page and tap "Enable Accessibility" button
    def enable_accessibility(self):
        # Verify Enable Accessibility Page
        root = self.verify_page("Enable_accessibility", "resource-id", "meter_done_tv")
        # Will verify text later
        # root = get_xml("Enable_Accessibility")
        # verify_text(root, "Enable_Accessibility_Text", "en-us", "resource-id", "meter_done_tv" )
        # verify_text(root, "Enable_Accessibility_button", "en-us", "resource-id", "meterdone_button" )
        # Tap "Enable Accessibility
        self.tap_this("En_AC_btn", "resource-id", "meterdone_button")
        self.logthis.write("enable_accessibility:: Tapped the Enabled Accessibility button\n")

    def enable_accessibility_native(self):
        # Verify Enable Accessibility Page
        root = self.verify_page("Enable_accessibility", "resource-id", "tv_common")
        # Will verify text later
        # root = get_xml("Enable_Accessibility")
        # verify_text(root, "Enable_Accessibility_Text", "en-us", "resource-id", "meter_done_tv" )
        # verify_text(root, "Enable_Accessibility_button", "en-us", "resource-id", "meterdone_button" )
        # Tap "Enable Accessibility
        self.tap_this("En_AC_btn", "resource-id", "btn_common")
        self.logthis.write("enable_accessibility:: Tapped the Enabled Accessibility button\n")

    # verify Done page and tap "DONE" button
    def done_page(self):
        # root = self.verify_page("DONE", "resource-id", "meterdone_button")
        # # Need to add translation in the excel file
        # # verify_text(root, "Done_body_text", "en-us", "resource-id", "meterdone_button")
        # # verify_text(root, "Done_button_text", "en-us", "resource-id", "meterdone_button" )
        # xy = self.get_xy(root, "resource-id", "meterdone_button")
        # x = xy[0]
        # y = xy[1]
        # self.tap(x, y)
        self.tap_this("DONE", "resource-id", "meterdone_button")
        # self.logthis.write("done_page:: Tapped the Done button\n")


    # To disconnect VPN (for LTVPN after pushing .e file)
    # IMPORTANT!!! need to escape the $ in the argument based on the OS running the script
    # For Windows escape with ^ for linux/unix escape with \
    def disconnect_vpn(self, VPN_name):
        self.adb(f"adb shell am start -n 'com.android.settings/.Settings\$VpnSettingsActivity'")
        # Tap VPN connection by name
        self.tap_this("VPN_Connection","text", VPN_name)
        self.tap_this("Disconnect", "resource-id", "button1")
        self.logthis.write("disconnect_vpn:: Disconnected the VPN connection")
        time.sleep(3)

    # Browse in default browser with url
    def browse(self, url):
        subprocess.call(f"adb shell am start -a android.intent.action.VIEW -d {url}",
                        shell=False)
        self.logthis.write(f"browse:: View the {url}\n")

    # Browse in Chrome with url
    def browse_samsung(self, url):
        subprocess.call(f"adb shell am start -n com.sec.android.app.sbrowser/.SBrowserMainActivity -d  {url}",
                        shell=False)
        self.logthis.write(f"browse_samsung:: Browsed the {url}\n")

    # Browse in Chrome with url
    def browse_chrome(self, url):
        subprocess.call(f"adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main -d {url}",
                        shell=False)
        self.logthis.write(f"browse_chrome:: Browsed the {url}\n")

    def browse_firefox(self, url):
        subprocess.call(f"adb shell am start -n org.mozilla.firefox/org.mozilla.gecko.BrowserApp - d {url}",
                        shell=False)
        self.logthis.write(f"browse_firefox:: Browsed the {url}\n")

    # This function will get the app usage log that is 2 hrs old and create two well-formed xml file
    # Copy app usage logs
    def get_appusage_log(self):
        # Create a dictionary for log file list
        app_usage_log = []
        app_usage_xml = []
        dirpath = '\\\\csiadots02\\e$\debug\\dcn.qa_mirror\\mobile'
        # get current date and format it to 20180724
        currDate = datetime.date.today()
        formattedCurrDate = currDate.strftime('%Y%m%d')
        # 24 hour diff
        d = timedelta(days=1)
        # Get yesterday date
        formattedYesterday = (currDate - d)
        formattedYesterday = formattedYesterday.strftime('%Y%m%d')
        # calculate past = 120 minutes
        past = time.time() - 60 * 60  # 2 hours
        # Loop with the file name with today date and time stamps that was modified in pass 120 minutes
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'mobile-{formattedCurrDate}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                app_usage_log.append(f_name)
        # Loop with the file name with yesterday date and time stamps that was modified in pass 120 minutes
        # This loop is for the log creation cut off time started at 7:59 PM
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'mobile-{formattedYesterday}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # append the file to the app_usage_log list
                app_usage_log.append(f_name)
        # copy app usage logs to the test directory
        for file in app_usage_log:
            shutil.copy(dirpath + "\\" + file, self.folder_path)
        # change working directory to test folder
        os.chdir(self.folder_path)
        # create app usage log object, this file will combine two app usage logs into one log file.
        with open("app_usage.txt", 'w', encoding="utf-8", errors='replace') as combine:
            for file in app_usage_log:
                with open(file, 'r', encoding='utf-8', errors='replace') as infile:
                    data = infile.read()
                    combine.write(data)
        # make a well-formed xml file
        with open('app_usage.txt', 'r', encoding='utf-8', errors='replace') as original:
            data = original.read()
            with open('app_usage.xml', 'w', encoding="utf-8", errors='replace') as modified:
                modified.write("<ROOT>\n" + data + "\n</ROOT>")

        app_usage_xml.append('app_usage.xml')
        # add root tag and make an well-formed xml file1
        #print(app_usage_xml)
        return app_usage_xml

    # Verify app usage data
    def verify_app_usage(self, bid, app):
        self.my_app_usage_logs = self.get_appusage_log()
        self.bid = '[@id="' + bid + '"]'
        self.logthis.write(f"\nThis is the beginning of the --{app}-- app launches verification.")
        app_start = {}
        x = 0
        for file in self.my_app_usage_logs:
            tree = ET.parse(file)
            root = tree.getroot()
            for submit in root.findall(f'./nsrecord/submit/{self.bid}/module[@type="application"]/data/node'):
                submit_dict = submit.attrib
                # print(submit_dict)
                # This will get the app usage data with app name, start time, end time
                if submit_dict.get("pkg") == app and submit_dict.get("e") == "start":
                    x += 1
                    self.logthis.write("verify_app_usage:: start: ")
                    self.logthis.write(submit_dict["st"])
                    self.logthis.write(" ")
                    self.logthis.write(submit_dict['title'])
                    self.logthis.write(" ")
                    self.logthis.write("End: ")
                    self.logthis.write(submit_dict['et'])
                    self.logthis.write("\nSeen ")
                    self.logthis.write(str(x))
                    self.logthis.write(f" time/s in the {file} as app is launched\n")
            if x > 0:
                self.logthis.write(f"verify_app_usage:: App --{app}-- 'start' is seen {x} time in the {file}. - PASSED\n\n")
            else:
                self.logthis.write(f"\nverify_app_usage:: App --{app}-- 'start' is not seen in the {file}. - FAILED\n")
        # This is for Installed app
        y = 0
        self.logthis.write(f"\nThis is the beginning of the app --{app}-- install verification.\n")
        for file in self.my_app_usage_logs:
            tree = ET.parse(file)
            root = tree.getroot()

            for submit in root.findall(f'./nsrecord/submit/{self.bid}/module[@type="application"]/data/node'):
                submit_dict = submit.attrib
                # This will get the app info if it is installed on the device and show up in the log
                if submit_dict.get("vendor") == app and submit_dict.get("e") == "install":
                    y += 1
                    self.logthis.write("verify_app_usage:: App: ")
                    self.logthis.write(submit_dict["e"])
                    self.logthis.write(" ")
                    self.logthis.write(submit_dict['app'])
                    self.logthis.write(" Version: ")
                    self.logthis.write(submit_dict['version'])
                    self.logthis.write(f"\nSeen 'installed'  in the app usage {file} {y} time/s.\n")
            if y > 0:
                self.logthis.write(f"verify_app_usage:: App --{app}-- 'install' is seen {y} time in the {file}. - PASSED\n")
            else:
                self.logthis.write(f"verify_app_usage:: App --{app}-- 'install' is not seen in the {file}. - FAILED\n")

    # Copy ci-24 logs
    def get_ci24_log(self):
        # Create a dictionary for log file list
        ci24_log = []
        # Shared location of the log file
        dirpath = '\\\\csiadots02\\e$\\debug\\dcn.qa_mirror\\cid-mobv2'
        # get current date and format it to 20180724
        currDate = datetime.date.today()
        formattedCurrDate = currDate.strftime('%Y%m%d')
        # 24 hour diff
        d = timedelta(days=1)
        # Get yesterday date
        formattedYesterday = (currDate - d)
        formattedYesterday = formattedYesterday.strftime('%Y%m%d')
        # calculate past = 120 minutes
        past = time.time() - 60 * 60  # 2 hours
        # Loop with the file name with today date and time stamps that was modified in pass 120 minutes
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'cid-mobv2-{formattedCurrDate}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # append the file name to the list
                ci24_log.append(f_name)
        # Loop with the file name with yesterday date and time stamps that was modified in pass 120 minutes
        # This loop is for the log creation cut off time started at 7:59 PM
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'mobile-{formattedYesterday}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # Append the file name to the list
                ci24_log.append(f_name)
        for file in ci24_log:
            shutil.copy(dirpath + "\\" + file, self.folder_path)

        os.chdir(self.folder_path)
        # add root tag and make an well-formed xml file1

        with open("ci_24.txt", 'w') as combine:
            for file in ci24_log:
                with open(file, 'r') as infile:
                    data = infile.read()
                    combine.write(data)
        # make a well-formed xml file
        with open('ci_24.txt', 'r') as original:
            data = original.read()
            with open('ci_24.xml', 'w') as modified:
                modified.write("<ROOT>\n" + data + "\n</ROOT>")
        ci24_xml_file = 'ci_24.xml'
        # add root tag and make an well-formed xml file1
        return ci24_xml_file

    def verify_ci_24(self, split_bid, url):
        log = self.get_ci24_log()
        # print(log)
        # Parse XML
        tree = ET.parse(log)
        # get to the root of the xml file
        root = tree.getroot()
        self.logthis.write(f"\nverify_ci_24::This is the beginning of the ci=24 {url} data verification \n")
        x = 0
        ci_final =""
        txt_dict_final = ""
        al_text_final = ""
        for ns in root.iter('nsrecord'):
            for n_s in ns.iter('al'):
                al_text = n_s.text
                if al_text == split_bid:
                    for u_d in  ns.iter('udata'):
                        u_data_dict = u_d.attrib
                        ci = u_data_dict['ci']
                        for txt in u_d.iter('text'):
                            txt_dict = txt.text
                            # print(txt_dict)
                            if txt_dict in url and ci == "24":
                                x += 1
                                ci_final = ci
                                al_text_final = al_text
                                txt_dict_final = txt_dict
        if x < 1:
            self.logthis.write(f"verify_ci_24:: Ci=24 data is missing for {url} - FAILED\n")
        else:
            self.logthis.write(f"verify_ci_24:: Ci- {ci_final} data for {txt_dict_final} is found for {al_text_final}. - PASSED\n")

    def ci_24_with_count(self, split_bid, url):
        log = self.get_ci24_log()
        # print(log)
        # Parse XML
        tree = ET.parse(log)
        # get to the root of the xml file
        root = tree.getroot()
        self.logthis.write(f"\nci_24_with_count:: This is the beginning of the ci=24 {url} data verification \n")
        x = 0
        ci_final = ""
        txt_dict_final = ""
        al_text_final = ""
        for ns in root.iter('nsrecord'):
            for n_s in ns.iter('al'):
                al_text = n_s.text
                if al_text == split_bid:
                    for u_d in  ns.iter('udata'):
                        u_data_dict = u_d.attrib
                        ci = u_data_dict['ci']
                        for txt in u_d.iter('text'):
                            txt_dict = txt.text
                            # print(txt_dict)
                            if txt_dict in url and ci == "24":
                                x += 1
                                ci_final = ci
                                al_text_final = al_text
                                txt_dict_final = txt_dict
                                self.logthis.write(f"ci_24_with_count:: {x}. -- {txt_dict} -- was under Ci-{ci} tag for {al_text} in this log.\n ")
        if x < 1:
            self.logthis.write(f"ci_24_with_count:: Ci=24 data is missing for {url} - FAILED\n")
        else:
            self.logthis.write(f"ci_24_with_count:: Ci- {ci_final} data for {txt_dict_final} is found for {al_text_final} {x} times in total. - PASSED\n")

# Get LTVPN log for source 3 and 5
    def get_ltvpn_log(self):
        # Create a dictionary for log file list
        ltvpn_log = []
        # Shared location of the log file
        dirpath = '\\\\csiadots02\\e$\\debug\\dcn.qa_mirror\\client-mobv2'
        # get current date and format it to 20180724
        currDate = datetime.date.today()
        formattedCurrDate = currDate.strftime('%Y%m%d')
        # 24 hour diff
        d = timedelta(days=1)
        # Get yesterday date
        formattedYesterday = (currDate - d)
        # calculate past = 120 minutes
        past = time.time() - 60 * 60  # 2 hours
        # Loop with the file name with today date and time stamps that was modified in pass 120 minutes
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'client-mobv2-{formattedCurrDate}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # append the file name to the list
                ltvpn_log.append(f_name)
        # Loop with the file name with yesterday date and time stamps that was modified in pass 120 minutes
        # This loop is for the log creation cut off time started at 7:59 PM
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'mobile-{formattedYesterday}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # Append the file name to the list
                ltvpn_log.append(f_name)
        for file in ltvpn_log:
            shutil.copy(dirpath + "\\" + file, self.folder_path)

        os.chdir(self.folder_path)
        # add root tag and make an well-formed xml file1
        with open("ltvpn_log.txt", 'w') as combine:
            for file in ltvpn_log:
                with open(file, 'r') as infile:
                    data = infile.read()
                    combine.write(data)
        # make a well-formed xml file
        with open('ltvpn_log.txt', 'r') as original:
            data = original.read()
            with open('ltvpn_log.xml', 'w') as modified:
                modified.write("<ROOT>\n" + data + "\n</ROOT>")
        ltvpn_xml_file = 'ltvpn_log.xml'
        # add root tag and make an well-formed xml file1
        return ltvpn_xml_file

    # Get csproxy info

    # Verify LTVPN source 3 and 5 data
    def verify_ltvpn_data(self, split_bid, source, address):
        log = self.get_ltvpn_log()
        # Parse XML
        tree = ET.parse(log)
        # get to the root of the xml file
        root = tree.getroot()
        self.logthis.write(f"\n\nThis is the beginning of the LTVPN {address} data verification \n")
        x = 0
        y = 0
        for ns in root.iter('nsrecord'):
            oss_text = ""
            url_text = ""
            al_text = ""
            rc_text = ""
            ns_attr = ns.attrib
            url_source = ns_attr['source']
            # print(url_source)
            for req in ns.iter('request'):
                while y == 0:
                    for oss in req.iter('oss'):
                        oss_text= oss.text
                        y += 1
                        self.logthis.write(f"csproxy info:  {oss_text}\n")
                for al in req.iter('al'):
                    al_text = al.text

                for url in req.iter('url'):
                    url_text = url.text

            for reply in ns.iter('reply'):
                for rc in reply.iter('rc'):
                    rc_text = rc.text
            # print(al_text)
            # print(rc_text)
            # print(url_text)
            if url_source == source and url_text in address and rc_text == "200" and al_text == split_bid:
                x += 1
                self.logthis.write(
                    f"verify_ltvpn_data:: {x} Found the {url_text}, for {al_text} with source {url_source} and response was {rc_text} - PASSED.\n ")
        if x < 1:
            self.logthis.write(f"verify_ltvpn_data:: Source {source} for {address} is not found in the {log}. - FAILED\n")

    # Verify LTVPN source 3 and 5 data This
    # This is for counting the ltvpn data to compare with DTLS data
    def verify_ltvpn_source(self, split_bid, source):
        log = self.get_ltvpn_log()
        # log = self.apk_Path + '\\' + 'ltvpn_log.xml'
        # Parse XML
        tree = ET.parse(log)
        # get to the root of the xml file
        root = tree.getroot()
        self.logthis.write(f"\n\nThis is the beginning of the LTVPN source only verification \n")
        x = 0
        for ns in root.iter('nsrecord'):
            url_text = ""
            al_text = ""
            rc_text = ""
            sb_text = ""
            rb_text = ""
            ns_attr = ns.attrib
            url_source = ns_attr['source']
            # print(url_source)
            for req in ns.iter('request'):
                for al in req.iter('al'):
                    al_text = al.text
                for url in req.iter('url'):
                    url_text = url.text
                for sb in req.iter('sb'):
                    sb_text = sb.text

            for reply in ns.iter('reply'):
                for rc in reply.iter('rc'):
                    rc_text = rc.text
                for rb in reply.iter('rb'):
                    rb_text = rb.text
            # print(al_text)
            # print(rc_text)
            # print(url_text)
            if url_source == source and al_text == split_bid:
                x += 1
                self.logthis.write(
                    f"verify_ltvpn_data:: {x} Found the {url_text} for {al_text} with source {url_source} and response was {rc_text} - PASSED.\n ")
        if x < 1:
            self.logthis.write(f"verify_ltvpn_data:: Source {source} for ltvpn data is not found in the {log}. - FAILED\n")

    # copy DTLS log from the server
    def get_dtls_log(self):
        # Create a dictionary for log file list
        dtls_log = []
        # Shared location of the log file
        dirpath = '\\\\10.106.33.132\\mproxy'
        # get current date and format it to 20180724
        currDate = datetime.date.today()
        formattedCurrDate = currDate.strftime('%Y%m%d')
        # 24 hour diff
        d = timedelta(days=1)
        # Get yesterday date
        formattedYesterday = (currDate - d)
        # calculate past = 120 minutes
        past = time.time() - 60 * 120  # 2 hours
        # Loop with the file name with today date and time stamps that was modified in pass 120 minutes
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'ns{formattedCurrDate}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # Append the file name in the list
                dtls_log.append(f_name)
        # Loop with the file name with yesterday date and time stamps that was modified in pass 120 minutes
        # This loop is for the log creation cut off time started at 7:59 PM
        for f_name in os.listdir(dirpath):
            if f_name.startswith(f'mobile-{formattedYesterday}_') and f_name.endswith('.log') and os.path.getmtime(
                    dirpath + "\\" + f_name) >= past:
                # Append the file name in the list
                dtls_log.append(f_name)
        # Copy log file to the test folder
        for file in dtls_log:
            shutil.copy(dirpath + "\\" + file, self.folder_path)
        # Change directory to local test folder
        os.chdir(self.folder_path)
        # Combine log files into 1 log file
        with open("dtls_log.txt", 'w') as combine:
            for file in dtls_log:
                with open(file, 'r') as infile:
                    data = infile.read()
                    combine.write(data)
        dtls_log = "dtls_log.txt"
        # return the log file
        return dtls_log

    # Verify DTLS data
    def verify_dtls_data(self, bid, url):
        self.logthis.write(f"\nverify_dtls_data:: This is the DTLS data verification for: {url}\n")
        log = self.get_dtls_log()
        with open(log, 'r') as f:
            my_regex = r"\b(?=\w)" + re.escape(bid) + r"\b(?!\w)"
            with open('dtls_bid.txt', 'a+') as f1:
                lines = f.readlines()
                for line in lines:
                    if re.search(my_regex, line, re.IGNORECASE):
                        f1.write(line)
        with open("dtls_bid.txt", 'r', errors='ignore') as log:
            x = 0
            for text in log:
                bid_index = (text.find(bid))
                http_index = (text.find("http"))
                HTTP_index = text.find("HTTP/1.1")
                ci = text[:bid_index - 1]
                URL = text[http_index: HTTP_index - 1]
                response_code = text[HTTP_index + 9:HTTP_index + 12]
                if bid_index > 0 and URL in url and response_code == "200":
                    x += 1
                    self.logthis.write(f"veirfy_dtls_data:: {x}. {ci} data for {URL} with response {response_code} was found in dtls_bid.txt - PASSED\n")
            if x < 1:
                self.logthis.write(
                    f"veirfy_dtls_data:: {url} data for {bid} was not found in dtls_bid.txt - FAILED\n")

    def verify_dtls_source_only(self, bid):
        log = self.get_dtls_log()
        with open(log, 'r') as f:
            my_regex = r"\b(?=\w)" + re.escape(bid) + r"\b(?!\w)"
            with open('dtls_bid.txt', 'a+') as f1:
                lines = f.readlines()
                for line in lines:
                    if re.search(my_regex, line, re.IGNORECASE):
                        f1.write(line)
        with open("dtls_bid.txt", 'r', errors='ignore') as log:
            self.logthis.write(f"\nverify_dtls_data:: This is the DTLS data verification for: {bid}\n")
            x = 0
            for text in log:
                bid_index = (text.find(bid))
                http_index = (text.find("http"))
                HTTP_index = text.find("HTTP/1.1")
                ci = text[:bid_index - 1]
                URL = text[http_index: HTTP_index - 1]
                response_code = text[HTTP_index + 9:HTTP_index + 12]
                if ci == "6-8":
                    x += 1
                    self.logthis.write(f"veirfy_dtls_data:: {x}. {ci} data for {bid} with {URL} and response {response_code} was found in dtls_bid.txt - PASSED\n")
            if x < 1:
                self.logthis.write(
                    f"veirfy_dtls_data:: 6-8 data for {bid} was not found in dtls_bid.txt - FAILED\n")
        with open("dtls_bid.txt", 'r', errors='ignore') as log:
            self.logthis.write(f"\nverify_dtls_data:: This is the DTLS data verification for: {bid}\n")
            y = 0
            for text in log:
                bid_index = (text.find(bid))
                http_index = (text.find("http"))
                HTTP_index = text.find("HTTP/1.1")
                ci = text[:bid_index - 1]
                URL = text[http_index: HTTP_index - 1]
                response_code = text[HTTP_index + 9:HTTP_index + 12]
                if ci == "7-8":
                    y += 1
                    self.logthis.write(f"veirfy_dtls_data:: {y}. {ci} data for {bid} with {URL} and response {response_code} was found in dtls_bid.txt - PASSED\n")
            if y < 1:
                self.logthis.write(
                    f"veirfy_dtls_data:: 7-8 data for {bid} was not found in dtls_bid.txt - FAILED\n")

    # Delete XML file used in the test to reduce the test folder size
    def delete_xml(self):
        os.chdir(self.folder_path)
        xml_file_list = os.listdir(self.folder_path)
        for file in xml_file_list:
            if file.endswith(".xml"):
                os.remove(file)

    # COpy your test folder to the shared
    def move_to_share(self):
        self.logthis.write(f"move_to_share:: {self.folder_name} will be copied over to the shared.\n")
        shutil.copytree(self.folder_path, self.shared_path + "\\" + "results" + "\\" + self.folder_name)

    # Get x coordinate of the device
    def get_x(self):
        output = self.adb("adb shell dumpsys window displays")
        # output = subprocess.check_output("adb shell dumpsys window windows | grep -E mCurrentFocus", shell=True)
        output = str(output)
        new_str = None
        myscreen = None
        # print(output)
        str_index = (output.find('cur='))
        if str_index > 0:
            # print(output[str_index:])
            new_str = output[str_index:]
        str_end = (new_str.find(' '))
        if str_end > 0:
            myscreen = (new_str[:str_end])
        # print(myscreen)
        equal_index = myscreen.find('=')
        x_index = myscreen.find('x')
        # x value
        x = myscreen[equal_index + 1:x_index]
        return x

    # Get y coordinate of the device
    def get_y(self):
        output = self.adb("adb shell dumpsys window displays")
        # output = subprocess.check_output("adb shell dumpsys window windows | grep -E mCurrentFocus", shell=True)
        output = str(output)
        new_str = None
        myscreen = None
        # print(output)
        str_index = (output.find('cur='))
        if str_index > 0:
            # print(output[str_index:])
            new_str = output[str_index:]
        str_end = (new_str.find(' '))
        if str_end > 0:
            myscreen = (new_str[:str_end])
        x_index = myscreen.find('x')
        # y value
        y = myscreen[x_index + 1:]
        # print(x)
        # print(y)
        return y

    # This will tap using x and y coordinates, it is calculated based on Huawei P9 device.
    def tap_xy(self, x, y):
        x_axis = int(self.get_x())
        y_axis = int(self.get_y())
        a = x * x_axis / 1080
        b = y * y_axis / 1920
        device_model = self.adb("adb devices -l")
        device_model = str(device_model, 'UTF-8')
        if "SAMSUNG_SM_N910A" in device_model or "SM_G920T" in device_model:
            b += 120
        self.adb(f'adb shell input tap {a} {b}')
        time.sleep(2)

    # To change device language
    def change_language(self, languageID):
        self.logthis.write(f"Device language is now set to: {languageID}.\n")
        self.adb("adb shell pm grant net.sanapeli.adbchangelanguage android.permission.CHANGE_CONFIGURATION")
        self.adb(f"adb shell am start -n net.sanapeli.adbchangelanguage/.AdbChangeLanguage -e language {languageID}")
        print(f"Device language is now set to: {languageID}.\n")


    def check_if_present_no_root(self, root, attr, item):
        x = False
        # Check the page is there or not
        for text in root.iter("node"):
            # This will create a dictionary for each nodes
            xml_dict = text.attrib
            if item in xml_dict[attr]:
                print("check_if_present:: " + item + " is present.\n")
                self.logthis.write("check_if_present:: " + item + " is present.\n")
                x = True
                break
        return x

    # Enable Accessibility and press done in one call
    def complete_acc(self, ACC_app_name):
        x = 0
        self.enable_accessibility()
        time.sleep(3)
        self.verify_page("App_ACC_Inst", "package", "com.android.settings")
        while self.check_if_present("ACC_app_name", "text", ACC_app_name) == False and x < 4:
            self.scroll_down_m()
            x += 1
        self.tap_this("ACC_app_name", "text", ACC_app_name)
        time.sleep(3)
        root = self.verify_page("APP_ACC_page", "text", ACC_app_name)
        self.tap_this_no_root(root, "class", "android.widget.Switch")
        time.sleep(3)
        root = self.verify_page("Use_app_name", "resource-id", "alertTitle")
        self.tap_this_no_root(root, "resource-id", "button1")
        time.sleep(2)
        self.tap_this("DONE", "resource-id", "meterdone_button")

    def complete_acc_native(self, ACC_app_name):
        x = 0
        self.enable_accessibility_native()
        time.sleep(3)
        self.verify_page("App_ACC_Inst", "package", "com.android.settings")
        while self.check_if_present("ACC_app_name", "text", ACC_app_name) == False and x < 4:
            self.scroll_down_m()
            x += 1
        self.tap_this("ACC_app_name", "text", ACC_app_name)
        time.sleep(3)
        root = self.verify_page("APP_ACC_page", "text", ACC_app_name)
        self.tap_this_no_root(root, "class", "android.widget.Switch")
        time.sleep(3)
        root = self.verify_page("Use_app_name", "resource-id", "alertTitle")
        self.tap_this_no_root(root, "resource-id", "button1")
        time.sleep(2)
        self.tap_this("DONE", "resource-id", "btn_common")

    # Allow VPN in one call
    def allow_vpn(self):
        root = self.verify_page("VPN_Permission_prompt", "package", "com.android.vpndialogs")
        self.tap_this_no_root(root, "resource-id", "button1")

    # To clear existing notifications
    def clear_notifications(self):
        x = 0
        while x < 5:
            self.adb( f"adb shell service call statusbar 1")
            if self.check_if_present("Clear_Text", "text", "Clear"):
                time.sleep(2)
                self.tap_this("Clear_button", "text", "Clear")
                break
            elif self.check_if_present("Clear_All", "content-desc", "Clear all notifications"):
                time.sleep(2)
                self.tap_this("CLear_All", "content-desc", "Clear all")
                break
            else:
                self.scroll_down_l()
                x += 1
        #subprocess.call(f"adb shell service call statusbar 2", shell=False)

    def get_multi_text(self, root, attr, item):
        my_list = []
        x = 0
        for text in root.iter("node"):
            # this will create a dictionary for each node
            xml_dict = text.attrib
            if item in xml_dict[attr]:
                my_list.append(xml_dict['text'])
                x += 1
        if x > 0:
            print(my_list)
            return my_list
        # If for loop didn't find it print the missing
        else:
            print(item + " is missing on the screen")
            self.logthis.write(f"get_multi_text:: + {item} not found on the screen.\n")
            self.screenshot_only(item)
            return "TEXT_NOT_FOUND"

    def get_multi_text2(self, root):
        my_list = []
        x = 0
        for text in root.iter("node"):
            # this will create a dictionary for each node
            xml_dict = text.attrib
            my_list.append(xml_dict['text'])
            x += 1
        return my_list

    def verify_multi_text(self, root, translation_excel, key, language):
        # get ref text
        ref = self.get_ref_text(translation_excel, key, language)
        app_text = self.get_multi_text2(root)
        print(app_text)
        z = len(app_text)
        x = 0
        w = 0
        y = 0
        for text in app_text:

            if ref == text:
                w += 1
                x += 1
                print(key + " text matched! PASSED")
                self.logthis.write(f"verify_multi_text:: Round: {w} verification - \n")
                self.logthis.write(f"verify_multi_text:: {key} text macthed! - PASSED\n")
                break
            else:
                y += 1
                w += 1
                print(f"verify_multi_text:: Round: {x} verification -")
                print(key + " text didn't match: FAILED")
                if y == z:
                    self.logthis.write(f"verify_multi_text:: Round: {w} verification - \n")
                    self.logthis.write("verify_multi_text:: Expected: " + ref + "\n")
                    self.logthis.write("verify_multi_text:: Actual: " + text + "\n")

    # To verify notification text
    def verify_notification(self, test_app, key, language):
        x = 0
        while x < 3:
            self.adb(f"adb shell service call statusbar 1")
            if self.check_if_present("Notification", "text", test_app):
                root = self.get_xml("Notification")
                self.verify_multi_text(root, self.translation_excel, key, language)
                self.logthis.write(f"verify_notification:: Notification found, please see the text verification result above this line.\n")
                self.adb(f"adb shell service call statusbar 2")
                break
            else:
                self.scroll_down_m()
                x += 1
        if x >= 3:
            self.logthis.write(f"verify_notification:: There is no notification associated with {test_app} - FAILED\n")
            self.adb(f"adb shell service call statusbar 2")

    # Get battery level of the device
    def get_battery_level(self):
        self.logthis.write(f"\n++++++++ Battery Level +++++++++++\n")
        try:
            output = self.adbshell("adb shell dumpsys battery | grep level")
            output = str(output, 'UTF-8')
            time_now = datetime.datetime.now()
            time_now = time_now.strftime("%m-%d-%y_%H-%M-%S")
            self.logthis.write(f"\nAt {time_now}- Battery level is: {output}\n")
        except subprocess.CalledProcessError:
            self.logthis.write(f"\nError occured while getting battery level\n")

    # uninstall MX apps
    def uninstall_mx_apps(self):
        self.uninstall("com.voicefive.ultra")
        self.uninstall("com.voicefive.mms")
        self.uninstall("com.voicefive.swissmediapanel")

    # get network connectivity information of the device adb shell dumpsys connectivity | grep -i NetworkAgentInfo
    def get_connectivity_info(self):
        self.logthis.write(f"\n++++++++ VPN and Wi-Fi connection Status +++++++++++\n\n")
        wifi_out1 = self.adbshell("adb shell dumpsys wifi | grep 'Wi-Fi is'")
        wifi_out1 = str(wifi_out1, 'UTF-8')
        self.logthis.write(f"{wifi_out1}\n")
        wifi_out2 = self.adbshell("adb shell dumpsys wifi | grep 'mNetworkInfo'")
        wifi_out2 = str(wifi_out2, 'UTF-8')
        self.logthis.write(f"{wifi_out2}\n")
        try:
            output = self.adbshell("adb shell dumpsys connectivity | grep -i 'VPN ()'")
            output = str(output, 'UTF-8')
            self.logthis.write(f"{output}\n")
        except subprocess.CalledProcessError:
            self.logthis.write("VPN is not connected\n")

    # # Connect to country with HMA
    # def connect_hma(self, country):
    #     location = country + ","
    #     self.force_stop("com.hidemyass.hidemyassprovpn")
    #     time.sleep(2)
    #     subprocess.call(f"adb shell monkey -p com.hidemyass.hidemyassprovpn 1", shell=False)
    #     time.sleep(2)
    #     root=self.get_xml("HMA_Start")
    #     self.tap_this_no_root(root,"resource-id", "location_mode")
    #     time.sleep(2)
    #     if self.check_if_present("ChooseLocation", "resource-id", "change_location_button") == True:
    #         self.tap_this("ChangeLocation", "resource-id", "change_location_button")
    #     else:
    #         self.tap_this("ChangeLocation", "resource-id", "choose_location_button")
    #     time.sleep(2)
    #     self.tap_this("All", "resource-id", "button_all")
    #     time.sleep(2)
    #     self.tap_this("Search", "content-desc", "Search")
    #     self.enter_text(country)
    #     time.sleep(2)
    #     self.enter_key()
    #     time.sleep(2)
    #     self.hide_keyboard()
    #     time.sleep(2)
    #     self.tap_this("Country", "text", location)
    #     time.sleep(2)
    #     if self.check_if_present("Feedback", "resource-id", "positiveButton") == True:
    #         self.tap_this("Perfect", "resource-id", "positiveButton")
    #     if self.check_if_present("Feedback", "resource-id", "remindMeLaterButton") == True:
    #         self.tap_this("RemindMeLater", "resource-id", "remindMeLaterButton")
    #     if self.check_if_present("Connected", "resource-id", "state_text") == True:
    #         print(f"HMA is now connected to {country}")
    #         self.logthis.write(f"connect_hma:: HMA is now connected to {country}.\n")
    #
    # # disconnect HMA
    # def disconnect_hma(self):
    #     self.tap_this("Disconnect", "resource-id", "state_text")
    #     print("Disconnecting HMA VPN connection")
    #     self.logthis.write(f"connect_hma:: HMA is disconnecting.\n")
