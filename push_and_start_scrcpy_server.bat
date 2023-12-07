adb push scrcpy-server /data/local/tmp/scrcpy-server-manual.jar
adb forward tcp:10038 localabstract:scrcpy
adb shell CLASSPATH=/data/local/tmp/scrcpy-server-manual.jar app_process / com.genymobile.scrcpy.Server 2.1.1 tunnel_forward=true audio=false control=false video_codec=h264 cleanup=false send_device_meta=false send_frame_meta=true send_dummy_byte=false send_codec_meta=false max_size=720 video_codec_options=profile=1,level=2 power_on=true

