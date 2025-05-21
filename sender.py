import asyncio
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import TcpSocketSignaling
from av import VideoFrame
import fractions
from datetime import datetime

ice_servers = [
    RTCIceServer(urls="stun:stun.l.google.com:19302"),
    RTCIceServer(urls="stun:stun1.l.google.com:19302"),
    RTCIceServer(urls="stun:stun2.l.google.com:19302"),
    RTCIceServer(urls="stun:stun3.l.google.com:19302"),
    RTCIceServer(urls="stun:stun4.l.google.com:19302")
]

class Stats():
    def __init__(self):
        self.stats_outbound_rtp = {}
        self.stats_inbound_rtp = {}
        self.stats_outbound_rtcp = {}
        self.stats_inbound_rtcp = {}
        self.stats_transport = {}

    async def update_stats(self, report: dict):
        report_type = report.get("type")
        if report_type is not None:
            if "outbound-rtp" in report_type:
                self.stats_outbound_rtp.update(report)
            elif "inbound-rtp" in report_type:
                self.stats_inbound_rtp.update(report)
            elif "outbound-rtcp" in report_type:
                self.stats_outbound_rtcp.update(report)
            elif "inbound-rtcp" in report_type:
                self.stats_inbound_rtcp.update(report)
            elif "transport" in report_type:
                self.stats_transport.update(report)



class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id, stats: Stats):
        super().__init__()
        self.cap = cv2.VideoCapture(camera_id)
        self.frame_count = 0
        self.stats = stats

    async def recv(self):
        self.frame_count += 1
        print(f"Sending frame {self.frame_count}")
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera")
            return None
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        #video_frame.pts = self.frame_count
        #video_frame.time_base = fractions.Fraction(1, 30)  # Use fractions for time_base
        # Add timestamp to the frame
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Current time with milliseconds
        cv2.putText(frame, f'{timestamp}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, 30)  # Use fractions for time_base
        return video_frame
    

async def fetch_webrtc_stats(peer_connection: RTCPeerConnection, stats_obj):
    """
    Periodically fetch WebRTC stats from the given RTCPeerConnection.
    
    :param peer_connection: Instance of aiortc.RTCPeerConnection
    """
    try:
        while True:
            # Fetch WebRTC stats
            stats = await peer_connection.getStats()
            
            # Print or process the stats
            for report in stats.values():
                # Convert report to a dictionary by manually extracting its fields
                report_dict = {
                    "id": report.id,
                    "type": report.type,
                    "timestamp": report.timestamp,
                }
                
                # Dynamically add all other attributes from the report object
                additional_fields = {
                    attr: getattr(report, attr)
                    for attr in dir(report)
                    if not attr.startswith("_")  # Exclude private attributes
                    and attr not in report_dict  # Avoid overwriting existing keys
                    and not callable(getattr(report, attr))  # Exclude methods
                }
                report_dict.update(additional_fields)

                print("Processed Report:", report_dict)
                await stats_obj.update_stats(report_dict)
            
            # Wait for 1 second before fetching again
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("WebRTC stats fetching has been cancelled.")
    except Exception as e:
        print(f"Error fetching WebRTC stats: {e}")


async def setup_webrtc_and_run(ip_address, port, camera_id, stats: Stats, iceServers=ice_servers):
    signaling = TcpSocketSignaling(ip_address, port)
    configuration = RTCConfiguration(iceServers=iceServers)
    pc = RTCPeerConnection(configuration=configuration)
    video_sender = CustomVideoStreamTrack(camera_id, stats)
    pc.addTrack(video_sender)
    stats_task = asyncio.create_task(fetch_webrtc_stats(pc, stats))
    
    try:
        await signaling.connect()

        @pc.on("datachannel")
        def on_datachannel(channel):
            print(f"Data channel established: {channel.label}")

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"Connection state is {pc.connectionState}")
            if pc.connectionState == "connected":
                print("WebRTC connection established successfully")

        @pc.on("iceconnectionstatechange")
        def on_iceconnectionstatechange():  
            print(f"ICE connection state changed: {pc.iceConnectionState}")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await signaling.send(pc.localDescription)

        while True:
            obj = await signaling.receive()
            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)
                print("Remote description set")
            elif obj is None:
                print("Signaling ended")
                break
        print("Closing connection")
    finally:
        await pc.close()

async def main():
    ip_address = "127.0.0.1" # Ip Address of Remote Server/Machine
    #ip_address = "192.168.133.135"
    #ip_address = "192.168.133.247"
    port = 20000
    camera_id = 0 # Change this to the appropriate camera ID
    stats = Stats()
    await setup_webrtc_and_run(ip_address, port, camera_id, stats, iceServers=ice_servers)

if __name__ == "__main__":
    asyncio.run(main())