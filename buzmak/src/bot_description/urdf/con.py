#!/usr/bin/env python

import rospy
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion, quaternion_from_euler
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from sensor_msgs.msg import Image, CameraInfo
import cv2, cv_bridge
import time
import math


class Control():

    def __init__(self, robot_name="robot"):
        rospy.init_node('robot_control_node')

        self.vel_publisher = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
        self.cmd = Twist()        

        self.laser_subscriber = rospy.Subscriber('/laser/scan', LaserScan, self.laser_callback)
        self.laser_msg = LaserScan() 

        self.sub_odom = rospy.Subscriber ('/odom', Odometry, self.get_rotation)
        
        self.rate = rospy.Rate(30)

        self.bridge = cv_bridge.CvBridge()
        self.image_sub = rospy.Subscriber('/camera_link/image_raw', Image, self.image_callback)
        #follower = Follower()

    def image_callback(self, msg):
        image = self.bridge.imgmsg_to_cv2(msg,desired_encoding='bgr8')
        self.hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
        # h,w,c=image.shape 
        cv2.imshow("image window", image)
        cv2.waitKey(1)        

    roll = pitch = yaw = 0.0
    target = 90
    kp=1.7

    def get_rotation (self, msg):
        global roll, pitch, yaw
        orientation_q = msg.pose.pose.orientation
        orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
        (roll, pitch, yaw) = euler_from_quaternion (orientation_list)

    def publish_once_in_cmd_vel(self):
        self.vel_publisher.publish(self.cmd)

    def laser_callback(self, msg):
        self.laser_msg = msg

    def get_laser(self, pos):
        return self.laser_msg.ranges[pos]

    def get_laser_full(self):
        return self.laser_msg.ranges

    def stop(self):
        self.cmd.linear.x = 0
        self.cmd.angular.z = 0
        self.publish_once_in_cmd_vel()

    def move_forward(self):

        self.cmd.linear.x = 0.5
        self.cmd.linear.y = 0
        self.cmd.linear.z = 0
        self.cmd.angular.x = 0
        self.cmd.angular.y = 0
        self.cmd.angular.z = 0

        self.publish_once_in_cmd_vel()

    def correction_left(self):
        self.cmd.linear.x = 0.5
        self.cmd.linear.y = 0
        self.cmd.linear.z = 0
        self.cmd.angular.x = 0
        self.cmd.angular.y = 0
        self.cmd.angular.z = 1

        self.publish_once_in_cmd_vel()

    def correction_right(self):
        self.cmd.linear.x = 0.5
        self.cmd.linear.y = 0
        self.cmd.linear.z = 0
        self.cmd.angular.x = 0
        self.cmd.angular.y = 0
        self.cmd.angular.z = -1

        self.publish_once_in_cmd_vel()

    def turn_left(self, turn_angle):
        turn_angle=turn_angle+1
        if turn_angle==3:
            turn_angle=-1
        return turn_angle

    def turn_right(self, turn_angle):
        turn_angle=turn_angle-1
        if turn_angle==-2:
            turn_angle=2
        return turn_angle

    def uturn(self, turn_angle):
        turn_angle=turn_angle+1
        if turn_angle==3:
            turn_angle=-1
        turn_angle=turn_angle+1
        if turn_angle==3:
            turn_angle=-1
        return turn_angle

    def turn(self, turn_angle):
        print(turn_angle)
        m=bool(1)
        while  m:
            target_rad = self.target*math.pi*turn_angle/180
            self.cmd.angular.z = self.kp * (target_rad-yaw)
            self.vel_publisher.publish(self.cmd)
            #print("taeget={} current:{}", target_rad,yaw)
            self.rate.sleep()
            if round(target_rad,1)==round(yaw,1):
                m=0
                self.stop()
               # print ('povernul!')


if __name__ == '__main__':
    
    robot = Control()
    flag=1
    turn_angle=0
    for i in range(10):
        robot.rate.sleep()
    robot.turn(turn_angle)
    print(robot.get_laser(359))
    while flag:
        if robot.get_laser(359)>1.5 and robot.get_laser(719)<2:
            if robot.get_laser(479)<1.7:
                robot.correction_right()
                robot.rate.sleep()
            if robot.get_laser(239)<1.7:
                robot.correction_left()
                robot.rate.sleep()
            robot.move_forward()
            #print('vpered! \n', robot.get_laser(359))
            robot.rate.sleep()

        if robot.get_laser(0) > 10 and robot.get_laser(359) > 10 and robot.get_laser(719) >10:
            print('Done!')
            robot.stop()
            flag = 0
            break

        if robot.get_laser(719)>2:
            robot.stop()
            turn_angle=robot.turn_left(turn_angle)
            if robot.get_laser(359)<3:
                while robot.get_laser(359)>1.5:
                    robot.move_forward()
                    robot.rate.sleep()
            else:
                for i in range(5):
                    robot.move_forward()
                    robot.rate.sleep()
            robot.turn(turn_angle)
            print('Turn Left\n')
            for i in range(150):
                robot.move_forward()
                robot.rate.sleep()
        
        if robot.get_laser(719)<1.3 and robot.get_laser(359)<1.3 and robot.get_laser(0)<1.5:
            print('Lidar: ', robot.get_laser(0), robot.get_laser(359), robot.get_laser(719))
            robot.stop()
            turn_angle=robot.uturn(turn_angle)
            robot.turn(turn_angle)
            robot.move_forward()
            print('U-Turn\n')
            #robot.stop()
        print('Lidar: ', robot.get_laser(0), robot.get_laser(359), robot.get_laser(719))
        if robot.get_laser(719)<2 and robot.get_laser(359)<1.5 and robot.get_laser(0)>2.7:
            robot.stop()
            turn_angle=robot.turn_right(turn_angle)
            robot.turn(turn_angle)
            print('Turn Right\n')
            #robot.stop()
        
    