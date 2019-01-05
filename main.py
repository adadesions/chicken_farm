import sys
import cv2
import pyzed.sl as sl
import numpy as np


def print_camera_information(cam):
    print("Resolution: {0}, {1}.".format(round(cam.get_resolution().width, 2), cam.get_resolution().height))
    print("Camera FPS: {0}.".format(cam.get_camera_fps()))
    print("Firmware: {0}.".format(cam.get_camera_information().firmware_version))
    print("Serial number: {0}.\n".format(cam.get_camera_information().serial_number))


def init_cam():
    camera_settings = sl.CAMERA_SETTINGS.CAMERA_SETTINGS_BRIGHTNESS
    str_camera_settings = "BRIGHTNESS"
    step_camera_settings = 1

    init_params = sl.InitParameters()
    init_params.depth_mode = sl.DEPTH_MODE.DEPTH_MODE_PERFORMANCE
    init_params.coordinate_units = sl.UNIT.UNIT_CENTIMETER

    cam = sl.Camera()
    if not cam.is_opened():
        print("Opening ZED Camera...")
    status = cam.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(repr(status))
        exit()

    return cam


def init_runtime():
    runtime = sl.RuntimeParameters()
    runtime.sensing_mode = sl.SENSING_MODE.SENSING_MODE_STANDARD

    return runtime


def frame_center(width, height):
    return (width//2, height//2)


def norm(x):
    sum_ = sum([k*k for k in x])

    return np.sqrt(sum_)


def create_circle(disp_img, center, distance, color=(0, 0, 255)):
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SIZE = 1

    cv2.circle(disp_img, center, 5, color, -1)

    if not np.isnan(distance) and not np.isinf(distance):
        print('distance:', distance, 'cm')
        cv2.circle(disp_img, center, np.int(distance-50), color, 2)
        cv2.putText(
            disp_img,
            '{} cm'.format(distance),
            (center[0], center[1]-30),
            FONT,
            FONT_SIZE,
            (0, 255, 0),
            2,
            cv2.LINE_AA
            )
    else:
        print("Can't estimate distance at this position, move the camera\n")
        cv2.circle(disp_img, center, 5, color, -1)
        cv2.putText(
            disp_img,
            '< 70 cm',
            (center[0], center[1]-10),
            FONT,
            FONT_SIZE,
            (0, 0, 255),
            2,
            cv2.LINE_AA
            )


def main():
    print("Running...")
    
    cam = init_cam()
    runtime = init_runtime()

    img = sl.Mat()
    depth = sl.Mat()
    point_cloud = sl.Mat()
    dx_list = [x for x in range(-400, 400, 300)]

    colors = []
    for i in range(len(dx_list)):
        colors.append(np.random.randint(0, 256, 3).tolist())

    key = ''


    while key != 113:
        err = cam.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:
            cam.retrieve_image(img, sl.VIEW.VIEW_LEFT)
            cam.retrieve_measure(depth, sl.MEASURE.MEASURE_DEPTH)
            cam.retrieve_measure(point_cloud, sl.MEASURE.MEASURE_XYZRGBA)
            
            disp_img = img.get_data()
            (cx, cy) = frame_center(img.get_width(), img.get_height())

            for dx, color in zip(dx_list, colors):
                error, pc = point_cloud.get_value(cx+dx, cy)
                distance = np.round(norm(pc[:3]), decimals=2)
                create_circle(disp_img, (cx+dx, cy), distance, color)


            # print('INFO: (x, y) = {}, {} | point_cloud = {}'.format(cx, cy, pc1))
            cv2.imshow("ZED", disp_img)
            key = cv2.waitKey(5)
        else:
            key = cv2.waitKey(5)
    
    cam.close()
    print('Closed camera')


if __name__ == '__main__':
    main()