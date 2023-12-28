from flask_socketio import Namespace
from flask_socketio import emit
import base64


class CameraNamespace(Namespace):
    def on_connect(self):
        print('Client connected')

    def video_frame(self, frame):
        frame_base64 = base64.b64encode(frame).decode('utf-8')
        print(f"Frame: {frame_base64}")
        emit('video_frame', {'frame': frame_base64})