import os
from onvif2 import ONVIFCamera, ONVIFService, ONVIFError

# wsdl path for the camera
current_file_path = os.path.abspath(os.path.dirname(__file__))
wsdl_dir = os.path.join(current_file_path, 'python-onvif2-zeep', 'wsdl')


# Create the camera object
mycam = ONVIFCamera('192.168.90.108', 80, 'admin', 'Bertek@206036', wsdl_dir)
media_service = mycam.create_media_service()
cam_token = media_service.GetProfiles()[0].token

# print key from profiles 
for profile in media_service.GetProfiles():
    print("--------> ")
    print(profile.Name, end=': ')
    print(profile.token)
    print(f"  {profile.VideoEncoderConfiguration.Resolution}")
    # get token
    cam_token = profile.token
    # get stream uri
    # stream_uri = self.media_service.GetStreamUri({'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}, 'ProfileToken': self.cam_token})

    stream_uri = media_service.GetStreamUri({'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}, 'ProfileToken': cam_token})
    # print url
    # self.url = f"rtsp://{self.user}:{self.password}@{stream_uri.Uri.split('//')[1]}"
    print(f"URI: {stream_uri}")
    print(f"Splitted: {stream_uri.Uri.split('//')[1]}")
    url = f"rtsp://admin:Bertek@206036@{stream_uri.Uri.split('//')[1]}" 
    print(url)

