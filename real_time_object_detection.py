# USAGE
# python real_time_object_detection.py --prototxt MobileNetSSD_deploy.prototxt.txt --model MobileNetSSD_deploy.caffemodel

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
from PIL import Image
import time
import numpy as np
import argparse
import imutils
import cv2
import requests

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prototxt", required=True,
                help="path to Caffe 'deploy' prototxt file")
ap.add_argument("-m", "--model", required=True,
                help="path to Caffe pre-trained model")
ap.add_argument("-c", "--confidence", type=float, default=0.2,
                help="minimum probability to filter weak detections")
ap.add_argument("-v", "--video_source", type=int, default=0,
                help="video source (default = 0, external usually = 1)")
args = vars(ap.parse_args())

# initialize the list of class labels MobileNet SSD was trained to
# detect, then generate a set of bounding box colors for each class
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# inisialisasi variabel
cek_vehicle = ""
watch = ""
persen_vehicle = 0

# load our serialized model from disk
print("[INFO] loading model...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

# initialize the video stream, allow the cammera sensor to warmup,
# and initialize the FPS counter
print("[INFO] starting video stream...")
# vs = VideoStream(src=args["video_source"]).start()
vs = VideoStream(src=args["video_source"]).start()
time.sleep(2.0)
fps = FPS().start()
d = 0


# function sent image to server

def sentImage(fileLokasi, nama, tipe, akurasi):
    url = 'https://taxparkir.id/api/vehicle/start_parkir'
    payload = {
        "name_vehicle": nama,
        "type_vehicle": tipe,
        "accuracy_vehicle": akurasi,
    }

    files = {
        "file": open(fileLokasi, "rb"),
    }

    response = requests.post(url, data=payload, files=files)
    # response.raise_for_status()
    res = response.json()
    # print(response.text)
    print("Status: {}".format(res))


# loop over the frames from the video stream
while True:
    # grab the frame from the threaded video stream and resize it
    # to have a maximum width of 400 pixels
    frame = vs.read()
    frame = imutils.resize(frame, width=400)

    # grab the frame dimensions and convert it to a blob
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

    # pass the blob through the network and obtain the detections and
    # predictions
    net.setInput(blob)
    detections = net.forward()

    # loop over the detections
    for i in np.arange(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the prediction
        confidence = detections[0, 0, i, 2]

        # filter out weak detections by ensuring the `confidence` is
        # greater than the minimum confidence
        if confidence > args["confidence"]:
            # extract the index of the class label from the
            # `detections`, then compute the (x, y)-coordinates of
            # the bounding box for the object
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # draw the prediction on the frame
            label = "{}: {:.0f}%".format(CLASSES[idx], confidence * 100)

            # inisialisasi type dan akurasi
            cek_vehicle = CLASSES[idx]
            persen_vehicle = confidence * 100

            # show the output akurasi dan type
            # print("object {}: {:.0f}".format(cek_vehicle, persen_vehicle))

            # show garis pada object (frame)
            cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            # show text pada object (frame)
            cv2.putText(frame, watch, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

    # show the output frame
    cv2.imshow("Frame", frame)

    # cek type car / motorbike & akurasi
    if "car" == cek_vehicle and persen_vehicle > 70:
        # crop image object
        crop_img = frame[startY:endY, startX:endX]

        # untuk menampilkan hasil crop image
        cv2.imshow("cropped", crop_img)

        tipe = cek_vehicle
        nama_kendaraan1 = 'mobil'
        akurasi = persen_vehicle

        # pause frame to 3 second
        cv2.waitKey(3000)

        # capture image from cropping
        # namaFile1 = cv2.imwrite("mobil%d.png"%d,crop_img)
        namaFile1 = "mobil_%d.png" % d
        fileLokasi = cv2.imwrite(namaFile1, crop_img)
        d += 1

        # sent image to server
        sentImage(namaFile1, nama_kendaraan1, tipe, persen_vehicle)

        # continue function
        continue
    # cek type car / motorbike & akurasi
    elif "motorbike" == cek_vehicle and persen_vehicle > 70:
        # crop image object
        crop_img = frame[startY:endY, startX:endX]

        # untuk menampilkan hasil crop image
        cv2.imshow("cropped", crop_img)

        tipe = cek_vehicle
        nama_kendaraan2 = 'motor'
        akurasi = persen_vehicle

        # pause frame to 3 second
        cv2.waitKey(3000)

        # capture image from cropping
        # namaFile = cv2.imwrite("motor%i.png"%i,crop_img)
        namaFile2 = "motor_%d.png" % d
        cv2.imwrite(namaFile2, crop_img)
        d += 1
        # sent image to server
        sentImage(namaFile2, nama_kendaraan2, cek_vehicle, persen_vehicle)

        # continue function
        continue
    key = cv2.waitKey(1) & 0xFF
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break
    # update the FPS counter
    fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elapsed time: {:.0f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.20}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()

