# -*- coding: utf-8 -*-
"""Attendence System.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1krmam60YK-4crk6WRhkjoVJCjZ1VrA5_
"""

!pip install --upgrade opencv-python
!pip install --upgrade opencv-python-headless

! pip install face_recognition

from IPython.display import display, Javascript
from google.colab.output import eval_js
from base64 import b64decode, b64encode
import numpy as np
import face_recognition as fr
import cv2
import csv
from datetime import datetime
import pytz
import os
import io
import time  # Import the time module
from PIL import Image

def video_stream():
    js = Javascript('''
        var video;
        var div = null;
        var stream;
        var captureCanvas;
        var imgElement;
        var labelElement;

        var pendingResolve = null;
        var shutdown = false;

        function removeDom() {
           stream.getVideoTracks()[0].stop();
           video.remove();
           div.remove();
           video = null;
           div = null;
           stream = null;
           imgElement = null;
           captureCanvas = null;
           labelElement = null;
        }

        function onAnimationFrame() {
          if (!shutdown) {
            window.requestAnimationFrame(onAnimationFrame);
          }
          if (pendingResolve) {
            var result = "";
            if (!shutdown) {
              captureCanvas.getContext('2d').drawImage(video, 0, 0, 640, 480);
              result = captureCanvas.toDataURL('image/jpeg', 0.8)
            }
            var lp = pendingResolve;
            pendingResolve = null;
            lp(result);
          }
        }

        async function createDom() {
          if (div !== null) {
            return stream;
          }

          div = document.createElement('div');
          div.style.border = '2px solid black';
          div.style.padding = '3px';
          div.style.width = '100%';
          div.style.maxWidth = '600px';
          document.body.appendChild(div);

          const modelOut = document.createElement('div');
          modelOut.innerHTML = "<span>Status:</span>";
          labelElement = document.createElement('span');
          labelElement.innerText = 'No data';
          labelElement.style.fontWeight = 'bold';
          modelOut.appendChild(labelElement);
          div.appendChild(modelOut);

          video = document.createElement('video');
          video.style.display = 'block';
          video.width = div.clientWidth - 6;
          video.setAttribute('playsinline', '');
          video.onclick = () => { shutdown = true; };
          stream = await navigator.mediaDevices.getUserMedia(
              {video: { facingMode: "environment"}});
          div.appendChild(video);

          imgElement = document.createElement('img');
          imgElement.style.position = 'absolute';
          imgElement.style.zIndex = 1;
          imgElement.onclick = () => { shutdown = true; };
          div.appendChild(imgElement);

          const instruction = document.createElement('div');
          instruction.innerHTML =
              '<span style="color: red; font-weight: bold;">' +
              'When finished, click here or on the video to stop this demo</span>';
          div.appendChild(instruction);
          instruction.onclick = () => { shutdown = true; };

          video.srcObject = stream;
          await video.play();

          captureCanvas = document.createElement('canvas');
          captureCanvas.width = 640; //video.videoWidth;
          captureCanvas.height = 480; //video.videoHeight;
          window.requestAnimationFrame(onAnimationFrame);

          return stream;
        }

        async function stream_frame(label, imgData) {
          if (shutdown) {
            removeDom();
            shutdown = false;
            return '';
          }

          var preCreate = Date.now();
          stream = await createDom();

          var preShow = Date.now();
          if (label != "") {
            labelElement.innerHTML = label;
          }

          if (imgData != "") {
            var videoRect = video.getClientRects()[0];
            imgElement.style.top = videoRect.top + "px";
            imgElement.style.left = videoRect.left + "px";
            imgElement.style.width = videoRect.width + "px";
            imgElement.style.height = videoRect.height + "px";
            imgElement.src = imgData;
          }

          var preCapture = Date.now();
          var result = await new Promise(function(resolve, reject) {
            pendingResolve = resolve;
          });
          shutdown = false;

          return {'create': preShow - preCreate,
                  'show': preCapture - preShow,
                  'capture': Date.now() - preCapture,
                  'img': result};
        }
        ''')

    display(js)

# Function to convert JavaScript reply to image
def js_to_image(js_reply):
    image_bytes = b64decode(js_reply.split(',')[1])
    jpg_as_np = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)
    return img

# Function to convert bounding box array to bytes
def bbox_to_bytes(bbox_array):
    bbox_PIL = Image.fromarray(bbox_array, 'RGBA')
    iobuf = io.BytesIO()
    bbox_PIL.save(iobuf, format='png')
    bbox_bytes = 'data:image/png;base64,{}'.format((str(b64encode(iobuf.getvalue()), 'utf-8')))
    return bbox_bytes

# Function to handle video frame processing
def video_frame(label, img_data):
    data = eval_js(f'stream_frame("{label}", "{img_data}")')
    return data

# Timezone for recording attendance
local_tz = pytz.timezone('Asia/Kolkata')

# Initialize attendance CSV file
date_str = datetime.now(local_tz).strftime("%Y-%m-%d")
filename = f"attendance_{date_str}.csv"

if not os.path.isfile(filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Designation', 'Department', 'Time', 'Date'])

known_face_encodings = []
known_face_names = []
image_paths_dict = {
    'Gautam Adani': ["/content/adani.jpg", "/content/adani1.jpg", "/content/adani2.jpg", "/content/adani3.jpg", "/content/adani4.jpg"],
    'Bill Gates': ["/content/bill.jpg", "/content/bill1.jpg", "/content/bill2.jpg", "/content/bill3.jpg", "/content/bill4.jpg"],
    'Elon Musk': ["/content/elon.jpg", "/content/elon1.jpg", "/content/elon2.jpg", "/content/elon3.jpg", "/content/elon4.jpg"],
    'Steve Jobs': ["/content/jobs.jpg", "/content/jobs1.jpg", "/content/jobs2.jpg", "/content/jobs3.jpg", "/content/jobs4.jpg"],
    'Mukesh Ambani': ["/content/mukesh.jpg", "/content/mukesh1.jpg", "/content/mukesh2.jpg", "/content/mukesh3.jpg", "/content/mukesh4.jpg"],
    'Sharuk Khan': ["/content/srk.jpg", "/content/srk1.jpg", "/content/srk2.jpg", "/content/srk3.jpg"],
    'Sajal': ["/content/sajal.jpg"],
}

for name, image_paths in image_paths_dict.items():
    for image_path in image_paths:
        image = fr.load_image_file(image_path)
        try:
            encoding = fr.face_encodings(image)[0]
            known_face_encodings.append(encoding)
            known_face_names.append(name)
        except IndexError:
            print(f"No face found in {image_path}")

known_designations = {
    'Gautam Adani': 'CEO',
    'Bill Gates': 'Co-founder',
    'Elon Musk': 'Manager',
    'Steve Jobs': 'CTO',
    'Mukesh Ambani': 'Chairman',
    'Sharuk Khan': 'Actor',
    'Sajal': 'AI Engineer',
}

known_departments = {
    'Gautam Adani': 'Management',
    'Bill Gates': 'Technology',
    'Elon Musk': 'Marketing',
    'Steve Jobs': 'HR',
    'Mukesh Ambani': 'Finance',
    'Sharuk Khan': 'Entertainment',
    'Sajal': 'Research',
}

your_name = "Your Name"
your_department = "Your Department"
your_position = "Your Position"

local_tz = pytz.timezone('Asia/Kolkata')
date_str = datetime.now(local_tz).strftime("%Y-%m-%d")
filename = f"attendance_{date_str}.csv"

# Check if the file exists, create it with header if not
if not os.path.isfile(filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Designation', 'Department', 'Time', 'Date'])

attendance = {}
recognized_names = set()
video_stream()

label_html = 'Capturing...'
bbox = ''
frame_width = 640
frame_height = 480
line_height = 20

while True:
    js_reply = video_frame(label_html, bbox)
    if not js_reply:
        break

    current_datetime = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

    img = js_to_image(js_reply["img"])

    bbox_array = np.zeros([frame_height, frame_width, 4], dtype=np.uint8)

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    face_locations = fr.face_locations(rgb_img)
    face_encodings = fr.face_encodings(rgb_img, face_locations)

    messages = []
    line_offset = 0

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = fr.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if any(matches):
            face_distances = fr.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            name = known_face_names[best_match_index]
            designation = known_designations.get(name, "Unknown")
            department = known_departments.get(name, "Unknown")

            if name not in attendance:
                timestamp = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

                attendance[name] = [timestamp, designation, department]

                with open(filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([name, designation, department, timestamp.split()[1], timestamp.split()[0]])

                print(f"{name}'s attendance has been recorded.")
                recognized_names.add(name)
                messages.append(f"Attendance marked for {name}.")
            else:
                messages.append(f"Your attendance is already marked, {name}!")

            message_y = 39 + line_offset
            bbox_array = cv2.putText(bbox_array, messages[-1], (10, message_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
            line_offset += line_height

        else:
            messages.append("Person not recognized. Attendance cannot be marked.")

            message_y = 39 + line_offset
            bbox_array = cv2.putText(bbox_array, messages[-1], (10, message_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
            line_offset += line_height

        bbox_array = cv2.rectangle(bbox_array, (left, top), (right, bottom), (255, 0, 0), 1)

        if name != "Unknown":
            text = f'{name}, {designation}, {department}'
        else:
            text = f'{name}'

        bbox_array = cv2.putText(bbox_array, text, (left, bottom - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)

    bbox_array = cv2.putText(bbox_array, current_datetime, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)

    bbox_array[:, :, 3] = (bbox_array.max(axis=2) > 0).astype(int) * 255

    bbox_bytes = bbox_to_bytes(bbox_array)

    bbox = bbox_bytes

print("Video stream ended.")

