#!/bin/sh

DEST=192.168.42.22
#DEST=127.0.0.1
#VIDEO_CAPS="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)JPEG,payload=(int)96,ssrc=(uint)1006979985,clock-base=(uint)312170047,seqnum-base=(uint)3174"
#VIDEO_DEC="rtpjpegdepay ! jpegdec"
#RTPBIN_PARAMS="latency=250 drop-on-latency=true buffer-mode=1 ntp-sync=true"

RTPBIN_PARAMS="buffer-mode=0 do-retransmission=false drop-on-latency=true latency=250"
VIDEO_CAPS_MAIN="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)H264"
VIDEO_DEC_MAIN="rtph264depay ! avdec_h264 ! videorate"
VIDEO_SINK_MAIN="glupload ! glcolorconvert ! gloverlay location=rovergrid.png ! glimagesink sync=false"

VIDEO_CAPS_LINE="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)JPEG"
VIDEO_DEC_LINE="rtpjpegdepay ! jpegdec"
VIDEO_SINK_LINE="autovideosink"

gst-launch-1.0 -v --gst-debug-level=3 \
    rtpbin name=rtpbin $RTPBIN_PARAMS \
	udpsrc caps=$VIDEO_CAPS_LINE port=5000 ! rtpbin.recv_rtp_sink_0 \
        rtpbin. ! $VIDEO_DEC_LINE ! $VIDEO_SINK_LINE \
	udpsrc port=5001 ! rtpbin.recv_rtcp_sink_0 \
	rtpbin.send_rtcp_src_0 ! udpsink port=5005 host=$DEST sync=false async=false
