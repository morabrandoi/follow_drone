from rCNN.Model import DetectorAPI
import keyboard as ky
import cv2.cv2 as cv2  # for avoidance of pylint error
import tellopy
import numpy
import time
import sys
import av


# data handler for tellopy
def data_handler(event, sender, data, **args):
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        print(data)

# keyboard handlers
def press_key_handler(event):
    print(event.name)
    speed = 100
    if event.name == "t":
        drone.takeoff()
    if event.name == "w":
        drone.forward(speed)
    if event.name == "d":
        drone.right(speed)
    if event.name == "s":
        drone.backward(speed)
    if event.name == "a":
        drone.left(speed)
    if event.name == "up":
        drone.set_throttle(speed)
    if event.name == "down":
        drone.set_throttle(-speed)
    if event.name == "left":
        drone.counter_clockwise(speed)
    if event.name == "right":
        drone.clockwise(speed)
    if event.name == "n":
        drone.flip_backright()
    if event.name == "l":
        drone.land()

    if event.name == "q":
        global keep_going
        keep_going = False
        drone.quit()

def release_key_handler(event):
    print(event.name)
    speed = 0
    if event.name == "t":
        drone.takeoff()
    if event.name == "w":
        drone.forward(speed)
    if event.name == "d":
        drone.right(speed)
    if event.name == "s":
        drone.backward(speed)
    if event.name == "a":
        drone.left(speed)
    if event.name == "up":
        drone.set_throttle(speed)
    if event.name == "down":
        drone.set_throttle(-speed)
    if event.name == "left":
        drone.counter_clockwise(speed)
    if event.name == "right":
        drone.clockwise(speed)
    if event.name == "l":
        drone.land()

    if event.name == "q":
        global keep_going
        keep_going = False
        drone.quit()

def map_bounds_to_movement(box, img_height, img_width):
                    # y1       y2                    x1     x2
    mid_point = (int(((box[1]+box[3]) / 2)), int(((box[0]+box[2]) / 2)))
    box_width = box[3] - box[1]

    # measure left or right "ness" and map from 0 - 100, clockwise rotation or counter_clockwise
    yaw_speed_value = round(abs(1 - ((mid_point[0]+1) / (img_width // 2))) * 100)
    if mid_point[0] <= (img_width // 2):
        # person on left, turn counter_clockwise
        drone.counter_clockwise(yaw_speed_value)
    else:
        #person on right, turn clockwises
        drone.clockwise(yaw_speed_value)

    # back up if close, get close if far
    screen_ratio = box_width / img_width
    target_screen_ratio = 0.5
    longitudinal_speed_value = round((min(0.4, abs(target_screen_ratio - screen_ratio)) / 0.4) * 35)

    if screen_ratio < target_screen_ratio:
        drone.forward(longitudinal_speed_value)
    else:
        drone.backward(longitudinal_speed_value)

    # get low if high
    vert_speed_value = round(abs(1 - ((mid_point[1]+100) / (img_height // 2))) * 50)
    if mid_point[1] + 100 <= (img_height // 2):
        # go down if midpoint too low
        drone.down(vert_speed_value)
    else:
        # go up if midpoint too high
        drone.up(vert_speed_value)



# event listeners
ky.on_release(release_key_handler, suppress=True)
ky.on_press(press_key_handler, suppress=True)

model_path = './rCNN/frozen_inference_graph.pb'
odapi = DetectorAPI(path_to_ckpt=model_path)
threshold = 0.7

drone = tellopy.Tello()

try:
    drone.subscribe(drone.EVENT_FLIGHT_DATA, data_handler)
    drone.connect()
    drone.wait_for_connection(60.0)

    # skip first 100 frames
    frame_skip = 100
except Exception as e:
    print(e)

# ensuring container initializes
while 1:
    try:
        container = av.open(drone.get_video_stream())
        container
        break
    except Exception as e:
        print("sumthing wen wong xD rawrz\n")
        print(e)

        continue

global keep_going
keep_going = True


time_of_last_detect = time.time()
while keep_going:
    for frame in container.decode(video=0):
        if frame_skip > 0:
            frame_skip -= 1
            continue
        start_time = time.time()
        image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)

        # resizing
        height, width, _ = image.shape
        image = cv2.resize(image, (int(720 * width / height), 720))
        height, width, _ = image.shape

        # human detector part
        boxes, scores, classes, num = odapi.processFrame(image)

        # displaying bounding boxes amd midpoint dot
        for i in range(len(boxes)):
            # Class 1 represents human
            if classes[i] == 1 and scores[i] > threshold:
                time_of_last_detect = time.time()
                box = boxes[i]
                mid_point = (int(((box[1]+box[3]) / 2)), int(((box[0]+box[2]) / 2)))
                box_width = box[3] - box[1]
                cv2.rectangle(image, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 6)
                cv2.circle(image, mid_point, 1, (0, 255, 0), 3)
                map_bounds_to_movement(box, height, width)
                break
            elif time.time() - time_of_last_detect >= 4: # 4 seconds
                drone.forward(0)
                drone.left(0)
                drone.up(0)
                drone.clockwise(40)

        cv2.imshow("image", image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if frame.time_base < 1.0/60:
            time_base = 1.0/60
        else:
            time_base = frame.time_base
        frame_skip = int((time.time() - start_time)/time_base)
    else:
        if time.time() - time_of_last_detect > 12:
            search_for_human = True

cv2.destroyAllWindows()
