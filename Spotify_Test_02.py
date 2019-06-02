import datetime
import time
# This is importing the main python framework file, MyTest is the class name in the framework file 

from mobile_Tahir import MyTest
import os
from datetime import datetime


# I created this run_me() function so that I can launch this test by running "RunAll.py" script.
# That way you can ran multiple test one after another, Read more in the RunAll comment. 

def run_me():
    # Timer started
    start = datetime.now()
    # Create a test with ( app_name, test_folder_name, translation_file_name)
	# app_name = you can name whatever you want here, the name will be used in the first part of the test log file name. 
	# Below this line, MMS_TEST is the name of your test, it will be used to call the functions from the main framework. 
    MMS_TEST = MyTest("Spotify", "TestSuite1", "MMSstringstranslation.xlsx")
	
	# Those are the variables created in the main framework file and just importing these values to use in this test
    apk_Path = MMS_TEST.apk_Path
    logthis = MMS_TEST.logthis
    email = MMS_TEST.email
    translation_excel = MMS_TEST.translation_excel
    directory = MMS_TEST.directory
    ############################
    # assign apk file and package name here
	# you should assign the app you want to use in this test here
    ############################
    # set test app apk file and location, assuming we are testing the Spotify app
    test_app_apk = apk_Path + '\\' + "Spotify_8.4.64.555.apk"
    # test app package name
    test_app = "com.spotify.music"
    # meter config app apk file and location
    meterconfig_apk = apk_Path + '\\' + "MeterConfig-1.2.8-729967d-debug.apk"
    # meter config app package name
    meterconfig = "com.example.dporter.meterconfig"
    # Adb change language apk file ( will use this if play store installation failed for some reason
    ACL_app_apk = apk_Path + '\\' + "ADB_Change_Language_0.80.apk"
    # Adb change Language app package name
    ACL_app = "net.sanapeli.adbchangelanguage"
    # Whatsapp package name
    app_usage_01_apk = apk_Path + '\\' + "whatsapp Scanner_4.7.7.apk"
    # whatsapp package name
    app_usage_01 = "com.whatsapp"
    # Ebay apk file
    app_usage_02_apk = apk_Path + '\\' + "eBay_5.23.2.0.apk"
    # Ebay package name
    app_usage_02 = "com.ebay.mobile"
    # SnapChat apk file
    app_usage_04_apk = apk_Path + '\\' + "Snapchat_10.37.5.0.apk"
    # SnapChat package name
    app_usage_04 = "com.snapchat.android"
    # e file
    e_file = apk_Path + '\\' + "c06222004.e"
    # csproxy conf  file
    csroxy_conf = apk_Path + '\\' + "csproxy.conf"
    # e file location on device (etc folder)
    push_locatin = "/sdcard/Android/data/com.voicefive.ultra/files/etc"

    # Set the URL to visit
    url_1 = "https://www.cnn.com/"
    url_2 = "http://www.bbc.com/"
    url_3 = "https://www.target.com/"
	
	
    # Check if the device is connected or not
    MMS_TEST.check_device()
	# Wake up the device , turning the screen ON
    MMS_TEST.wake_up()
    # Android 7 and up unlock using the swype 
    MMS_TEST.swipe_unlock()
	# uninstall the existing test app 
	MMS_TEST.uninstall(test_app)
	# wait for 5 seconds 
	time.sleep(5)

	# sideload the test app 
    MMS_TEST.sideload(test_app, test_app_apk)
	# Check the internet connection
    MMS_TEST.check_connection()
	# Launch the spotify app (test_app)
	MMS_TEST.launch(test_app)
	# Browse yahoo.com with Chrome browser
	MMS_TEST.browse_chrome("www.yahoo.com")
	time.sleep(10)
	# This will force stop the Chrome browser
	MMS_TEST.force_stop("com.android.chrome")
	# Launch chrome and visit cnn.com
	MMS_TEST.browse_chrome("www.cnn.com")
	time.sleep(10)
	# Tap the home button
	MMS_TEST.tap_home() 
	# force stop the Spotify app
	MMS_TEST.force_stop(test_app)
    # Total time taken
    total_time = datetime.now() - start
	# Stopping the adb at the end of the test. You can use this to stop adb logging anywhere you want if you think adb is not needed
    MMS_TEST.stop_adb()
	# Writing to the test log, you can use this feature to write whatever you want in the test logs.
    logthis.write(f"\n\nTotal time taken to complete the test is (HH:MM:SS:SSSSSSS): {total_time}")
    MMS_TEST.get_app_version(test_app)
    # Closing the log file at the end of the test 
    logthis.close()
	# This is to clean up the xml file that we dumped from the device during the test. 
    MMS_TEST.delete_xml()
    # Send test summary email
    MMS_TEST.send_email("PASSED")
	# Tap Home button on the device 
    MMS_TEST.tap_home()
    print(directory)
    # This will change the current directory to where it was before the script started. Needed this to run multiple scripts
    os.chdir(directory)
    print("MMS_TEST completed")
