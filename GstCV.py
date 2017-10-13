import gi
import sys
import time
import numpy
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject, GLib
import cv2

class CVGstreamer:    
    def __init__(self, IP = '127.0.0.1', RTP_RECV_PORT = 5000, RTCP_RECV_PORT = 5001, RTCP_SEND_PORT = 5005):
        self.cvImage = None
        Gst.init(sys.argv)
        GObject.threads_init()        
        self.VIDEO_CAPS="application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)JPEG,payload=(int)26,ssrc=(uint)1006979985,clock-base=(uint)312170047,seqnum-base=(uint)3174"
        self.IP=IP
        self.RTP_RECV_PORT0=RTP_RECV_PORT
        self.RTCP_RECV_PORT0=RTCP_RECV_PORT     #
        self.RTCP_SEND_PORT0=RTCP_SEND_PORT     #
        self.PAUSED=False                       #

    def start(self):                            #
        if(self.PAUSED==True):                  #
            self.player.set_state(Gst.State.PLAYING)
            self.PAUSED=False
        else:                                   #
            self.initElements()
            self.linkElements()     
            self.player.set_state(Gst.State.READY)
            self.player.set_state(Gst.State.PAUSED)
            self.player.set_state(Gst.State.PLAYING) #
    
    def paused(self):                           #
        self.player.set_state(Gst.State.PAUSED)
        self.PAUSED=True

    def stop(self):                             #
        self.player.set_state(Gst.State.NULL)
        self.PAUSED=False
        print("STOP")       
    
    def on_error(self, bus, msg):
        err, dbg = msg.parse_error()
        print("ERROR:", msg.src.get_name(), ":", err.message)
        if dbg:
            print("Debug info:", dbg)

    
    def on_eos(self, bus, msg):
        print("End-Of-Stream reached")
        self.player.set_state(Gst.State.READY)

    
    def initElements(self):
        self.player = Gst.Pipeline.new("player")
        if not self.player:
            print("ERROR: Could not create pipeline.")
            sys.exit(1)
            
        self.bus=self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::error", self.on_error)
        self.bus.connect("message::eos", self.on_eos)

        ################ VIDEODEPAY ################################
        
        self.videodepay0=Gst.ElementFactory.make('rtpjpegdepay', 'videodepay0')
        if not self.videodepay0:
            print("ERROR: Could not create videodepay0.")
            sys.exit(1)

        ################  SOURCE  ##################################      
            
        self.rtpbin = Gst.ElementFactory.make('rtpbin', 'rtpbin')
        self.player.add(self.rtpbin)
        self.caps = Gst.caps_from_string(self.VIDEO_CAPS)

        def pad_added_cb(rtpbin, new_pad, depay):
            sinkpad = Gst.Element.get_static_pad(depay, 'sink')
            lres = Gst.Pad.link(new_pad, sinkpad)        
        
       
        self.rtpsrc0 = Gst.ElementFactory.make('udpsrc', 'rtpsrc0')
        self.rtpsrc0.set_property('port', self.RTP_RECV_PORT0)
    
        # we need to set caps on the udpsrc for the RTP data
        
        self.rtpsrc0.set_property('caps', self.caps)
    
        self.rtcpsrc0 = Gst.ElementFactory.make('udpsrc', 'rtcpsrc0')
        self.rtcpsrc0.set_property('port', self.RTCP_RECV_PORT0)

        self.rtcpsink0 = Gst.ElementFactory.make('udpsink', 'rtcpsink0')
        self.rtcpsink0.set_property('port', self.RTCP_SEND_PORT0)
        self.rtcpsink0.set_property('host', self.IP)
    
        # no need for synchronisation or preroll on the RTCP sink
        self.rtcpsink0.set_property('async', False)
        self.rtcpsink0.set_property('sync', False)
        self.player.add(self.rtpsrc0)
        self.player.add(self.rtcpsrc0)
        self.player.add(self.rtcpsink0)
        self.srcpad0 = Gst.Element.get_static_pad(self.rtpsrc0, 'src')
        
        self.sinkpad0 = Gst.Element.get_request_pad(self.rtpbin, 'recv_rtp_sink_0')
        self.lres0 = Gst.Pad.link(self.srcpad0, self.sinkpad0)
    
        # get an RTCP sinkpad in session 0
        self.srcpad0 = Gst.Element.get_static_pad(self.rtcpsrc0, 'src')
        self.sinkpad0 = Gst.Element.get_request_pad(self.rtpbin, 'recv_rtcp_sink_0')
        self.lres0 = Gst.Pad.link(self.srcpad0, self.sinkpad0)
    
        # get an RTCP srcpad for sending RTCP back to the sender
        self.srcpad0 = Gst.Element.get_request_pad(self.rtpbin, 'send_rtcp_src_0')
        self.sinkpad0 = Gst.Element.get_static_pad(self.rtcpsink0, 'sink')
        self.lres0 = Gst.Pad.link(self.srcpad0, self.sinkpad0)
            
        self.rtpbin.set_property('drop-on-latency', True)
        self.rtpbin.set_property('buffer-mode', 1)

        self.rtpbin.connect('pad-added', pad_added_cb, self.videodepay0)

############### DECODER ######################################
            
        self.decoder0 = Gst.ElementFactory.make('jpegdec', "decoder0")
        if not self.decoder0:
            print("ERROR: Could not create decoder0.")
            sys.exit(1)
       

######################## VIDEOCONVERT ############################
            
        self.videoconvert0 = Gst.ElementFactory.make("videoconvert", "videoconvert0")
        if not self.videoconvert0:
            print("ERROR: Could not create videoconvert0.")
            sys.exit(1)        

######################### CAPS AND SINK ###########################

        
        def gst_to_opencv(sample):
            buf = sample.get_buffer()
            caps = sample.get_caps()
            arr = numpy.ndarray(
                (caps.get_structure(0).get_value('height'),
                 caps.get_structure(0).get_value('width'),
                 3),
                buffer=buf.extract_dup(0, buf.get_size()),
                dtype=numpy.uint8)
            return arr

        def new_buffer(sink, data):
            sample = sink.emit("pull-sample") 
            arr = gst_to_opencv(sample)
            self.cvImage = arr          # openCV image
            return Gst.FlowReturn.OK

        self.sink = Gst.ElementFactory.make("appsink", "sink")
        if not self.sink:
            print("ERROR: Could not create sink.")
            sys.exit(1)

        caps = Gst.caps_from_string("video/x-raw, format=(string){BGR, GRAY8}")
        self.sink.set_property("caps", caps)

        self.sink.set_property("emit-signals", True)
        self.sink.connect("new-sample", new_buffer, self.sink)


######################### VIDEOSCALE ##################################
        
        self.videoscale0 = Gst.ElementFactory.make("videoscale", "videoscale0")
        if not self.videoscale0:
            print("ERROR: Could not create videoscale0.")
            sys.exit(1) 

##################################################################        
        self.player.add(self.videodepay0)
        self.player.add(self.decoder0)
        self.player.add(self.videoscale0)
        self.player.add(self.videoconvert0)        
        self.player.add(self.sink)

    def linkElements(self):
        link_ok = self.videodepay0.link(self.decoder0)
        if not link_ok:
            print("ERROR: Could not link videodepay0 with decoder0.")
            sys.exit(1)
       
        link_ok = self.decoder0.link(self.videoconvert0)
        if not link_ok:
            print("ERROR: Could not link decoder0 with videoconvert0.")
            sys.exit(1)

        link_ok = self.videoconvert0.link(self.videoscale0)
        if not link_ok:
            print("ERROR: Could not link videoconvert0 with videoscale0.")
            sys.exit(1)

        link_ok = self.videoscale0.link(self.sink)
        if not link_ok:
            print("ERROR: Could not link videoscale0 with sink.")
            sys.exit(1)



        


