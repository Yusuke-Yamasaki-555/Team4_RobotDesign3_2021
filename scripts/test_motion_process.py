#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import rospy
import actionlib
import moveit_commander
import rosnode
from math import sin, cos, radians
from std_srvs.srv import SetBool
from team4_robotdesign3_2021.srv import SetInt32
from team4_robotdesign3_2021.msg import ActSignalFeedback, ActSignalResult, ActSignalAction
import geometry_msgs.msg

class ImageProcessServer:
    def __init__(self):
        self.srv_search_club = rospy.ServiceProxy('img_search_club', SetBool)
        self.srv_adjustx_club = rospy.ServiceProxy('img_adjustx_club', SetInt32)
        self.srv_adjusty_club = rospy.ServiceProxy('img_adjustxy_club', SetInt32)
        self.srv_search_target = rospy.ServiceProxy('img_search_target', SetBool)
        self.srv_adjustx_target = rospy.ServiceProxy('img_adjustx_target', SetInt32)
        self.srv_adjusty_target = rospy.ServiceProxy('img_adjusty_target', SetInt32)
    
class Motion_process:
    def __init__(self):
        self.arm = moveit_commander.MoveGroupCommander("arm")
        self.arm.set_max_velocity_scaling_factor(0.1)
        self.arm.set_max_acceleration_scaling_factor(1.0)
        self.gripper = moveit_commander.MoveGroupCommander("gripper")
        self.img_srv = ImageProcessServer()
        self.feedback = ActSignalFeedback()
        self.result = ActSignalResult()
        self.search_target_action_server = actionlib.SimpleActionServer('search_target', ActSignalAction, self.search_target, False)
        self.search_club_server = actionlib.SimpleActionServer('search_club', ActSignalAction, self.search_club, False)
        self.check_target_server = actionlib.SimpleActionServer('check_target', ActSignalAction, self.check_target)
        

    # def release_club_motion(self,<クライアントから送られるデータ名>):

    # この関数では、release_club をする動作をServiceとして提供する
    # 動作の速度＆加速度の比率を定義
    # 動作を行う(test.py参照)
    # 動作の完了報告を返す

    # def swing_club_motion(self,<クライアントから送られるデータ名>):

    # この関数では、swing_club をする動作をActionとして提供する
    # swing_set_club
    #     動作の速度＆加速度の比率を定義
    #     動作を行う(test.py参照)
    #     動作の完了報告をfeedback
    # swing_club
    #     動作の速度＆加速度の比率を定義
    #     動作を行う(test.py参照)
    #         ここで、印に当てるか外すかを決めてから、動作を行う
    #     動作の完了報告を返す

    def set_position(self, srdf_name):
        print("set")
        self.arm.set_named_target(srdf_name)
        self.arm.go()
        rospy.sleep(1.0)

    def search_target(self):
        self.set_position('search_target')
        for deg in range(-90, 90, 1):
            self.arm.set_joint_value_target({"crane_x7_shoulder_fixed_part_pan_joint":radians(deg)}) #根本を回転
            self.arm.go()
            search_res = self.img_srv.srv_search_target(True)
            if search_res.success:
                rospy.loginfo('Find_t')
                rospy.sleep(1.0)
                move = 0
                while True:
                    moveX = self.img_srv.srv_adjustx_target(377)
                    rospy.loginfo(moveX)
                    if moveX.int32Out == 0:
                        move = 0
                        break
                    move += 0.5*moveX.int32Out
                    self.arm.set_joint_value_target({"crane_x7_shoulder_fixed_part_pan_joint":radians(deg)-radians(move)}) #根本を回転
                    self.arm.go()
                rospy.sleep(1.0)
                while True:
                    moveY = self.img_srv.srv_adjusty_target(227)
                    rospy.loginfo(moveY)
                    if not moveY.int32Out:
                        move = 0
                        break
                    move += 0.5*moveY.int32Out
                    self.arm.set_joint_value_target({"crane_x7_upper_arm_revolute_part_rotate_joint":-1.75-radians(move)}) #根本を回転
                    self.arm.go()
                rospy.sleep(1.0)
        # self.set_position('init')
    
    def search_club(self):
        self.set_position('search_club')
        sum_deg = 0
        for deg in range(0, 110, 1):
            self.arm.set_joint_value_target({"crane_x7_shoulder_fixed_part_pan_joint":radians(deg)}) #根本を回転
            self.arm.go()
            search_res = self.img_srv.srv_search_club(True)
            # self.feedback.BoolFB = search_res
            # self.feedback.Int32FB = deg
            # self.search_club_server.publish_feedback(self.feedback)
            if search_res.success:
                print(f'deg = {deg}')
                rospy.loginfo('Find_c')
                move = 0
                while True:
                    moveX = self.img_srv.srv_adjustx_club(377)
                    move += 0.5*moveX.int32Out
                    self.arm.set_joint_value_target({"crane_x7_shoulder_fixed_part_pan_joint":radians(deg-move)}) #根本を回転
                    self.arm.go()
                    if moveX.int32Out == 0:
                        current_deg = radians(deg-move)
                        move = 0
                        break
                break
        print(f'deg={current_deg}')
        self.grip_club(current_deg = current_deg)
        # self.result.BoolRes = True
        # self.result.Int32Res = 
        # self.search_club_server.set_succeeded()
    
    def grip_club(self, current_deg):
        ABS_CLUB_POSITION = 0.25
        CLUB_Z_POSITION = 0.065 + 0.02
        arm_goal_pose = self.arm.get_current_pose().pose
        self.gripper.set_joint_value_target([0.9, 0.9])
        self.gripper.go()
        rospy.sleep(1.0)
        target_pose = geometry_msgs.msg.Pose()
        target_pose.position.x = ABS_CLUB_POSITION * cos(current_deg)
        target_pose.position.y = ABS_CLUB_POSITION * sin(current_deg)
        target_pose.position.z = CLUB_Z_POSITION
        target_pose.orientation.x = arm_goal_pose.orientation.x
        target_pose.orientation.y = arm_goal_pose.orientation.y
        target_pose.orientation.z = arm_goal_pose.orientation.z
        target_pose.orientation.w = arm_goal_pose.orientation.w
        self.arm.set_pose_target( target_pose )
        self.arm.go()
        self.gripper.set_joint_value_target([0.3, 0.3])
        self.gripper.go()
        self.arm.set_joint_value_target({"crane_x7_lower_arm_revolute_part_joint":0})
        self.arm.set_joint_value_target({"crane_x7_wrist_joint":-1.57})
        self.arm.go()
    
    def check_target(self):
        self.set_position('search_target')
        for deg in range(-90, 90, 1):
            self.arm.set_joint_value_target({"crane_x7_shoulder_fixed_part_pan_joint":radians(deg)}) #根本を回転
            self.arm.go()
            search_res = self.img_srv.srv_search_target(True)
            self.feedback.BoolFB = search_res
            self.feedback.Int32FB = deg
            if search_res.success:
                rospy.loginfo('Find_t')
                rospy.sleep(1.0)
                move = 0
                while True:
                    moveX = self.img_srv.srv_adjustx_target(377)
                    rospy.loginfo(moveX)
                    if moveX.int32Out == 0:
                        move = 0
                        break
                    move += 0.5*moveX.int32Out
                    self.arm.set_joint_value_target({"crane_x7_shoulder_fixed_part_pan_joint":radians(deg)-radians(move)}) #根本を回転
                    self.arm.go()
                rospy.sleep(1.0)
                while True:
                    moveY = self.img_srv.srv_adjusty_target(227)
                    rospy.loginfo(moveY)
                    if not moveY.int32Out:
                        move = 0
                        break
                    move += 0.5*moveY.int32Out
                    self.arm.set_joint_value_target({"crane_x7_upper_arm_revolute_part_rotate_joint":-1.75-radians(move)}) #根本を回転
                    self.arm.go()
                rospy.sleep(1.0)

def main():
    rospy.init_node("motion_process", anonymous=1)
    target = Motion_process()
    club = Motion_process()
    servers = ['img_search_club', 'img_adjustx_club', 'img_adjusty_club', 'img_search_target', 'img_adjustx_target', 'img_adjusty_target']
    while len([s for s in rosnode.get_node_names() if 'rviz' in s]) == 0:
        rospy.sleep(1.0)
    for server in servers:
        rospy.wait_for_service(server)
    
    # check_target_action_server = actionlib.SimpleActionClient('check_target', ActSignalAction, check.check_target, False)
    club.search_club()
    # target.search_target()

if __name__ == '__main__':
    try:
        if not rospy.is_shutdown():
            main()
    except rospy.ROSInterruptException as e:
        rospy.logerr(e)