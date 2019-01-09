import keyboard as ky
import cv2.cv2 as cv2  # for avoidance of pylint error
import traceback
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
        drone.flip_backRight()
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

# event listeners
ky.on_release(release_key_handler, suppress=True)
ky.on_press(press_key_handler, suppress=True)




drone = tellopy.Tello()

try:
    drone.subscribe(drone.EVENT_FLIGHT_DATA, data_handler)

    drone.connect()
    drone.wait_for_connection(60.0)

    container = av.open(drone.get_video_stream())
    # skip first 100 frames
    frame_skip = 100

except Exception as ex:
    print(ex)



global keep_going
keep_going = True

while keep_going:
    for frame in container.decode(video=0):
        if 0 < frame_skip:
            frame_skip = frame_skip - 1
            continue
        start_time = time.time()
        image = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
        cv2.imshow('Original', image)
        cv2.waitKey(1)

        if frame.time_base < 1.0/60:
            time_base = 1.0/60
        else:
            time_base = frame.time_base
        frame_skip = int((time.time() - start_time)/time_base)
