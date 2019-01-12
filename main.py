import cv2
import pyzed.sl as sl
import numpy as np
import time


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


def avg_distance(pixel_rect, threshold):
    len_ = len(pixel_rect)
    sum_ = 0
    for i, pixels in enumerate(pixel_rect):
        temp = norm(pixels)
        if temp < threshold:
            sum_ += temp
            print('dis:', temp)
        else:
            len_ -= 1

    try:
        return sum_/len_
    except ZeroDivisionError:
        return 0


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


def create_rect(disp_img, cx, cy, pts_cloud, diag=40, color=(0, 0, 255)):
        tl, tr = (cx-diag, cy-diag), (cx+diag, cy-diag)
        bl, br = (cx-diag, cy+diag), (cx+diag, cy+diag)
        cv2.rectangle(disp_img, tl, br, (0, 0, 255), 2)

        pixel_rect = []
        step = 10
        for col in range(tl[0], br[0]+1, step):
            for row in range(tl[1], br[1]+1, step):
                err, pixel = pts_cloud.get_value(col, row)
                pixel_rect.append(pixel[:3])

        avg_cm = avg_distance(pixel_rect, threshold=120)
        cv2.putText(
            disp_img,
            '{:.2f} cm'.format(avg_cm),
            tr,
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        return avg_cm


def main():
    print("Running...")
    
    cam = init_cam()
    runtime = init_runtime()

    img = sl.Mat()
    depth = sl.Mat()
    point_cloud = sl.Mat()
    dx_list = [x for x in range(0, 300, 300)]

    colors = []
    for i in range(len(dx_list)):
        colors.append(np.random.randint(0, 256, 3).tolist())

    key = ''

    while key != 113: # press 'q' to exit
        err = cam.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:
            # Recieve image and measurement
            cam.retrieve_image(img, sl.VIEW.VIEW_LEFT)
            cam.retrieve_measure(depth, sl.MEASURE.MEASURE_DEPTH)
            cam.retrieve_measure(point_cloud, sl.MEASURE.MEASURE_XYZRGBA)
            
            disp_img = img.get_data()
            (cx, cy) = frame_center(img.get_width(), img.get_height())


            # Drawing and Calculate area in rectangle
            avg_area1 = create_rect(disp_img, cx, cy, point_cloud, diag=40, color=(0, 0, 255))
            # avg_area2 = create_rect(disp_img, 300, 300, point_cloud, diag=40, color=(255, 0, 0))

            # Drawing Circle
            # for dx, color in zip(dx_list, colors):
            #     error, pc = point_cloud.get_value(cx+dx, cy)
            #     distance = np.round(norm(pc[:3]), decimals=2)
            #     create_circle(disp_img, (cx+dx, cy), distance, color)

            cv2.imshow("Chicken Farm", disp_img)
            key = cv2.waitKey(5)
            
            # Delay
            time.sleep(0.01)

            # Writing to disk
            with open('avg_log.txt', 'a') as file:
                file.writelines('{:.2f},\n'.format(avg_area1))
        else:
            key = cv2.waitKey(5)
    
    cam.close()
    print('Closed camera')


if __name__ == '__main__':
    main()