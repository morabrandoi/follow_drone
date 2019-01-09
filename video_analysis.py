from rCNN.Model import DetectorAPI
import numpy as np
import cv2
import time
import random


cap = cv2.VideoCapture('walking_sample.mp4')

model_path = './rCNN/frozen_inference_graph.pb'
odapi = DetectorAPI(path_to_ckpt=model_path)
threshold = 0.7

def map_bounds_to_movement(box, img_height, img_width):
                    # y1       y2                    x1     x2
    mid_point = (int(((box[1]+box[3]) / 2)), int(((box[0]+box[2]) / 2)))
    box_width = box[3] - box[1]
    # measure left or right "ness" and map from 0 - 100, clockwise rotation or counter_clockwise

    yaw_speed_value = round(abs(1 - ((mid_point[0]+1) / (img_width // 2))) * 100)
    if mid_point[0] <= (img_width // 2):
        # person on left, turn counter_clockwise
        print(f"drone.counter_clockwise({yaw_speed_value})")
    else:
        #person on right, turn clockwises
        print(f"drone.clockwise({yaw_speed_value})")

    # back up if close, get close if far
    screen_ratio = box_width / img_width
    target_screen_ratio = 0.4
    longitudinal_speed_value = round((min(0.4, abs(target_screen_ratio - screen_ratio)) / 0.4) * 100)

    if screen_ratio < target_screen_ratio:
        print(f"drone.forwards({longitudinal_speed_value})")
    else:
        print(f"drone.backwards({longitudinal_speed_value})")

time_of_last_detect = 0
while(cap.isOpened()):
    ret, image = cap.read()
    # resizing
    height, width, _ = image.shape
    image = cv2.resize(image, (int(720 * width / height), 720))
    height, width, _ = image.shape
    if random.choice([True, False]):
        continue
    # human detector part
    boxes, scores, classes, num = odapi.processFrame(image)

    # displaying bounding boxes amd midpoint dot
    for i in range(len(boxes)):
        # Class 1 represents human
        if classes[i] == 1 and scores[i] > threshold:
            search_for_human = False
            time_of_last_detect = time.time()
            box = boxes[i]
            mid_point = (int(((box[1]+box[3]) / 2)), int(((box[0]+box[2]) / 2)))
            box_width = box[3] - box[1]
            cv2.rectangle(image, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 6)
            cv2.circle(image, mid_point, 1, (0, 255, 0), 3)
            map_bounds_to_movement(box, height, width)
            break
    else:
        if time.time() - time_of_last_detect > 6:
            search_for_human = True

    cv2.imshow("image", image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
