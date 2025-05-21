# webrtc

This project demonstrates a simple WebRTC video streaming setup using Python's `aiortc` library. It consists of a sender and a receiver script for transmitting video frames over a network.

## Requirements

- Python 3.7+
- Install dependencies:
  ```sh
  pip install aiortc opencv-python av numpy
  ```

This will wait for a connection from the sender.

## Usage
### 1. Start the Sender
Run the sender script on the machine that has a webcam or video source:

```bash
python sender.py
```

By default, both scripts use `127.0.0.1` (localhost) and port `20000`.
To stream between different machines, update the ip_address variable in both scripts to use the appropriate network IPs.


### 2. Receiver

Similar to the sender code.
```bash
python sender.py
```

### Notes
- The sender captures video from the default camera (camera_id = 0). Change this value in sender.py if needed.
- Received frames are saved as images in the imgs/ directory by the receiver.
- Press q in the receiver window to exit. (Or kill it by pressing `Ctrl+C`)
- Recommendation: Use a conda environment