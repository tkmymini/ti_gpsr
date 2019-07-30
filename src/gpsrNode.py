#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from geometry_msgs.msg import Twist
import subprocess
from std_msgs.msg import String,Bool,Float64
from ti_gpsr.msg import array

class GPSRNode:
    def __init__(self):
        self.command_list_sub = rospy.Subscriber('/command_list',array,self.Command)
        self.navi_result_sub = rospy.Subscriber('/navigation/result',String,self.navigateResult)
        self.mani_result_sub = rospy.Subscriber('/object/grasp_res',Bool,self.manipulateResult)
        self.search_result_sub = rospy.Subscriber('/object/recog_res',Bool,self.searchResult)
        self.change_pose_res_sub = rospy.Subscriber('/arm/changing_pose_res',Bool,self.changePoseResult)
        #self.sentence_sub = rospy.Subscriber('',String,self.sentence)#未実装 
        
        self.destination_pub = rospy.Publisher('/navigation/destination',String,queue_size=1)
        self.search_pub = rospy.Publisher('/object/recog_req',String,queue_size=10)
        self.manipulation_pub = rospy.Publisher('/object/grasp_req',String,queue_size=10)
        self.changing_pose_req_pub = rospy.Publisher('/arm/changing_pose_req',String,queue_size=1)
        self.m6_reqest_pub = rospy.Publisher('/m6_controller/command',Float64,queue_size=1)
        self.gpsrAPI_pub = rospy.Publisher('/gpsrface',Bool,queue_size=10)#APIのON、OFF切り替え
        self.action_res_pub = rospy.Publisher('/command_res',Bool,queue_size=1)#動作の終了を知らせる

        #最低限必要な変数
        self.sub_state = 0
        self.task_count = 0
        self.action = 'none'
        self.location = 'none'
        self.obj = 'none'
        self.answer = 'none'
        self.sentence = 'null'#APIから直接の文章#未実装
        #各result
        self.navigation_result = 'null'
        self.search_result = False
        self.manipulation_result = False
        self.place_result = False
        #実行可能な動作リスト#このリストはcommand_listのループが必要なければこのリストはいらない
        self.com_list = ['go','grasp','search','speak','pass','place','end']
       
    def Command(self,command_list):
        #print 'action:{action} location:{location} obj:{obj} answer:{answer}'.format(action=command_list.action,location=command_list.location,obj=command_list.obj,answer=command_list.answer)#test
        #rospy.sleep(3)#test
        """for num in range(len(self.com_list)):#音声処理が正しくできていれば必要ない可能性大
            if self.com_list[num] in command_list.action:
                self.action = self.com_list[num]#command_list.action"""
        self.action = command_list.action
        #print 'action',self.action
        self.location = command_list.location
        self.obj = command_list.obj
        self.answer = command_list.answer
    
    def go(self):
        if self.sub_state == 0:
            self.m6_reqest_pub.publish(0.3)
            self.destination_pub.publish(self.location)
            self.sub_state = 1
        elif self.sub_state == 1:
            print 'navigation'
            if self.navigation_result == 'succsess':
                self.navigation_result = 'null'
                self.location = 'none'
                self.action = 'none'
                self.sub_state = 0
                self.action_res_pub.publish(True)

    def grasp(self):
        if self.sub_state == 0:
            self.m6_reqest_pub.publish(-0.07)
            self.manipulation_pub.publish(self.obj)
            self.sub_state = 1
        elif self.sub_state == 1:
            print 'manipulation'
            if self.manipulation_result == True:
                self.manipulation_result = False
                self.obj = 'none'
                self.action = 'none'
                self.sub_state = 0
                self.changing_pose_req_pub.publish('carry')
                rospy.sleep(3)
                self.action_res_pub.publish(True)
        
    def search(self):
        if self.sub_state == 0:
            self.m6_reqest_pub.publish(-0.07)
            self.search_pub.publish(self.obj)
            self.sub_state = 1
        elif self.sub_state == 1:
            print 'search'
            if self.search_result == True:
                CMD ='/usr/bin/picospeaker I find {obj}'.format(obj=self.obj)
                subprocess.call(CMD.strip().split(" "))
                rospy.sleep(3)#sentenceの長さによって変更
                self.search_result = False
                self.obj = 'none'
                self.action = 'none'
                self.sub_state = 0
                self.action_res_pub.publish(True)
            
    def speak(self):
        CMD ='/usr/bin/picospeaker {ans}'.format(ans=self.answer)
        subprocess.call(CMD.strip().split(" "))
        rospy.sleep(3)#sentenceの長さによって変更
        self.answer = 'none'
        self.action = 'none'
        self.action_res_pub.publish(True)
            
    def place(self):
        if self.sub_state == 0:
            self.changing_pose_req_pub.publish('place')
            self.sub_state = 1
        elif self.sub_state == 1:
            print 'put'
            if self.place_result == True:
                self.place_result = False
                self.action = 'none'
                self.sub_state = 0
                self.action_res_pub.publish(True)

    """def Pass(self):#音声仕様
        if self.sub_state == 0:
            self.changing_pose_req_pub.publish('pass')
            #rospy.sleep(2)動作に合わせて変更いらないかもしれない
            self.sub_state = 1
        elif self.sub_state == 1:
            CMD ='/usr/bin/picospeaker %s' % 'Here you are'
            subprocess.call(CMD.strip().split(" "))
            self.gpsrAPI_pub.publish(True)
            rospy.sleep(2)#sentenceの長さによって変更
            self.sub_state = 2
        elif self.sub_state == 2:
            if self.sentence == 'thank you':
                self.gpsrAPI_pub.publish(False)
                self.action = 'none'
                self.sub_state = 0
                self.action_res_pub.publish(True)"""

    """def Pass(self):#センサ値による仕様
        if self.sub_state == 0:
            self.changing_pose_req_pub.publish('pass')
            self.sub_state = 1
        elif self.sub_state == 1:
            print 'pass'
            if self.place_result == True:
                self.place_result = False
                self.action = 'none'
                self.sub_state = 0
                self.action_res_pub.publish(True)"""
                    
    def end(self):
        self.task_count+=1
        self.gpsrAPI_pub.publish(True)
        self.action ='none' 

    def finishState(self):
        if self.sub_state == 0:
            self.gpsrAPI_pub.publish(False)
            self.action = 'finish'
            self.destination_pub.publish('entrance')
            self.sub_state = 1
        elif self.sub_state == 1:
            print 'navi entrance'
            if self.navigation_result == 'succsess':
                CMD = '/usr/bin/picospeaker %s' % 'Finished gpsr'
                subprocess.call(CMD.strip().split(" "))
                print ''
                print 'finish GPSR'
                exit()
            
    def navigateResult(self,result):
        self.navigation_result = result.data
        print self.navigation_result

    def searchResult(self,result):
        self.search_result = result.data

    def manipulateResult(self,result):
        self.manipulation_result = result.data

    def changePoseResult(self,result):#現在[19/07/30]placeのみ
        self.place_result = result.data

    def sentence(self,sentence):#APIから直接sentenceを受け取る#未実装
        self.sentence = sentence.data

    def loopMain(self):
        print '///start GPSR//'
        while not rospy.is_shutdown():
            try:
                print ''
                print '--{action}-- [task_count:{count}]'.format(action=self.action,count=self.task_count)
                if self.task_count == 3:
                    self.finishState()
                if self.action == 'none':
                    if self.sub_state == 0:
                        CMD = '/usr/bin/picospeaker %s' % 'command waiting'
                        subprocess.call(CMD.strip().split(" "))
                        self.sub_state = 1
                elif self.sub_state == 1:
                    print "command waiting.."
                elif self.action != 'none':
                    self.sub_state = 0
                    self.gpsrAPI_pub.publish(False)
                    if self.action == "end":
                        self.end()
                    elif self.action == "go":
                        self.go()
                    elif self.action == "grasp":
                        self.grasp()
                    elif self.action == "search":
                        self.search()
                    elif self.action == "speak":
                        self.speak()              
                    elif self.action == "place":
                        self.place()              
                    elif self.action == "pass":
                        self.Pass()        
            except IndexError:
                pass
            rospy.sleep(0.5)    
    
if __name__ == '__main__':
    rospy.init_node('gpsr_node')
    gpsr = GPSRNode()
    rospy.sleep(1)
    gpsr.gpsrAPI_pub.publish(True)
    gpsr.action_res_pub.publish(True)#test用
    gpsr.loopMain()
    rospy.spin()
