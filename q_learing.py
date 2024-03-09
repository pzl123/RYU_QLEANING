# -*- coding:utf-8 -*-
"""
作者:${彭忠林}
日期:2023年06月01日
"""
import numpy as np
import pandas as pd
import random
import time  # 用来控制探索者速度有多快
import queue
import matplotlib.pyplot as plt
import os


class Q_LEARN:
    def __init__(self, delay, loss, jitter,yinzi=0.8,
                 EPSILON_increment=0.008,MAX_TIMES=200,
                 delay_ALPHA=0.2,loss_BETA=0.4,jitter_GAMMA=0.4,
                 EPSILON = 0,
                 ACTIONS=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],
                 N_STATES=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]):
        self.reward_delay_room = delay
        self.reward_loss_room = loss
        self.reward_jitter_room = jitter


        self.ACTIONS = ACTIONS
        self.N_STATES = N_STATES



        self.EPSILON = EPSILON # 贪婪度，即探索者有90%的情况会按照Q表的最优值选择行为，10%的时间会随机选择行为
        self.EPSILON_increment = EPSILON_increment
        self.MAX_EPSILON = 0.9
        self.ALPHA = yinzi  # 学习率，用来决定误差有多少需要被学习的，ALPHA是一个小于1的数
        self.GAMMA = 0.8  # 奖励递减值，表示对未来reward的衰减值
        self.MAX_TIMES = MAX_TIMES # 最大回合数

        self.delay_ALPHA = delay_ALPHA
        self.loss_BETA = loss_BETA
        self.jitter_GAMMA = jitter_GAMMA

        # q_table = pd.DataFrame(
        #     np.zeros((len(self.ACTIONS), len(self.N_STATES))),  # q_table为一个4x3的表格，并初始化值都为0
        #     columns=self.N_STATES,
        #     index=self.ACTIONS  # actions's name
        # )  # 建立一个q表，且初始值都为0

        self.reward_room_data = pd.read_excel('reward_room.xlsx',header=0,index_col=0)
        # print("初始化阶段reward_room is \n{}".format(self.reward_room_data))


    def build_q_table(self, n_states, actions):
        table = pd.DataFrame(
            np.zeros((len(n_states), len(actions))),  # q_table为一个4x3的表格，并初始化值都为0
            columns=n_states,
            index=actions  # actions's name
        )
        return table

    def max2min(self,data):
        # 因为delay是极小型，近来的数值确实极大型，进行极小极大转换，且归一化
        max_value = data.max().max()
        data = (max_value - data)/max_value
        return data

    def Normalization(self,data):
        min_value = data.min().min()
        max_value = data.max().max()
        # 归一化表格
        normalized_data = (data - min_value) / (max_value - min_value)
        return normalized_data

    def reward_room(self):
        self.reward_room_data = self.Normalization(self.delay_ALPHA * self.Normalization(self.max2min(self.reward_delay_room)) +
                                         self.loss_BETA * self.Normalization(self.max2min(self.reward_loss_room)) +
                                         self.jitter_GAMMA * self.Normalization(self.max2min(self.reward_jitter_room)))
        return self.reward_room_data

    def choose_action(self, state, q_table, EPSILON):
        # print("state in choose_action is {}".format(state))
        # print("state in choose_action type is {}".format(type(state)))
        # print("q_table in choose_action is \n{}".format(q_table))
        # 根据输入的状态及q表，输出动作
        state_actions = q_table.loc[[state], :]  # iloc函数提取行数据
        if (np.random.uniform() > EPSILON):  # 随机数大于0.9（即10%的时间会随机选择行为）或q表中某状态下左右两个动作的值都为0，此时随机选择动作
            if (state == 1 or state == 2):
                ACTIONS = [5,9,13,17]
            elif (state == 3 or state == 4):
                ACTIONS = [6,10,14,18]
            elif state == 5:
                ACTIONS = [1,7,8]
            elif state == 6:
                ACTIONS = [3,7,8]
            elif state == 7:
                ACTIONS = [5,6]
            elif state == 8:
                ACTIONS = [5,6]
            elif state == 9:
                ACTIONS = [1,2,11,12]
            elif state == 10:
                ACTIONS = [3,4,11,12]
            elif state == 11:
                ACTIONS = [9,10]
            elif state == 12:
                ACTIONS = [9,10]
            elif state == 13:
                ACTIONS = [1,2,15,16]
            elif state == 14:
                ACTIONS = [3,4,15,16]
            elif state == 15:
                ACTIONS = [13,14]
            elif state == 16:
                ACTIONS = [13,14]
            elif state == 17:
                ACTIONS = [1, 2, 19, 20]
            elif state == 18:
                ACTIONS = [3,4,19,20]
            elif state == 19:
                ACTIONS = [17,18]
            elif state == 20:
                ACTIONS = [17,18]
            action = random.choice(ACTIONS)
            # print("waiting in random")
        else:  # 随机数小于等于0.9（即探索者有90%的情况会按照Q表的最优值选择行为）
            action = int(state_actions.idxmax(axis=1).values)  # 在q表中取得该状态下值最大的动作的name
            # print("waiting in else")
            # print(state_actions.idxmax(axis=1).values)
            # print(state,action)
        # print(EPSILON)
        # print("action in choose_action is {}".format(action))
        # print("action in choose_action type is {}".format(type(action)))
        # print("----------one time-----------")
        return action

    def get_env_feedback(self, S, A, dst, path_):
        if (S == 1 or S == 2) and (A == 5 or A == 9 or A == 13 or A == 17):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 3 or S == 4) and (A == 6 or A == 10 or A == 14 or A == 18):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 5) and (A == 1 or A == 2 or A == 7 or A == 8):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 6) and (A == 3 or A == 4 or A == 7 or A == 8):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 7 or S == 8) and (A == 5 or A == 6):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 9) and (A == 1 or A == 2 or A == 11 or A == 12):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 10) and (A == 3 or A == 4 or A == 11 or A == 12):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 11 or S == 12) and (A == 9 or A == 10):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 13) and (A == 1 or A == 2 or A == 15 or A == 16):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 14) and (A == 3 or A == 4 or A == 15 or A == 16):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 15 or S == 16) and (A == 13 or A == 14):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 17) and (A == 1 or A == 2 or A == 19 or A == 20):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 18) and (A == 3 or A == 4 or A == 19 or A == 20):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        elif (S == 19 or S == 20) and (A == 17 or A == 18):
            R = self.reward_room_data.loc[S, A]
            S_ = A
        else:
            R = -1
            S_ = S

        if S_ in path_:
            R = -0.8

        if S_ == dst:
            R = 1

        # print('结尾S_ is %d',S_)
        return S_, R


    def rl(self,src, dst):
        print('-------------------MAX_TIEMS is {}-------'.format(self.MAX_TIMES))
        # q-learning的主要部分
        self.reward_room_data = self.reward_room()
        leiji_reward = []
        step_s = []
        path_list = []
        if os.path.isfile('./table./q_table.xlsx'):
            q_table = pd.read_excel('./table./q_table.xlsx',index_col=0)
        else:
            q_table = pd.DataFrame(
                np.zeros((len(self.ACTIONS), len(self.N_STATES))),  # q_table为一个4x3的表格，并初始化值都为0
                columns=self.N_STATES,
                index=self.ACTIONS # actions's name
            )  # 建立一个q表，且初始值都为0
        print('开始训练')

        # print(q_table)
        for time in range(self.MAX_TIMES):  # 训练 MAX_EPISODES 个回合
            reward = 0
            S = src  # 初始化探索者的状态（位置）
            S_ = S  # 初始化后一刻状态
            path_ = []
            path_.append(S)
            step_s.append(time)
            while (S != dst):
                A = self.choose_action(S, q_table, self.EPSILON)  # 选择动作

                S_, R = self.get_env_feedback(S=S, A=A, dst=dst, path_=path_)  # 根据当前的状态及动作，获取下一状态和奖励

                # q_table = update_q_table(S,A,R,S_,q_table,dst) #更新Q表
                q_predict = float((q_table.loc[[S], [A]]).values)  # 根据当前的状态及动作，取出当前q表中对应位置的值，即Q估计
                # print(S,A)
                # q_predict = q_table.loc[[S],[A]]# 当使用 .iloc[row_index, column_index] 访问 DataFrame 中的元素时，行和列的索引都应该从 0 到 N-1，其中 N 是对应维度的长度。
                # print(q_predict)
                if S_ != dst:
                    q_target = R + self.GAMMA * q_table.loc[S_, :].max()
                    # print(q_target)
                else:
                    q_target = R
                # print(q_target - q_predict)
                q_table.loc[[S], [A]] += self.ALPHA * (q_target - q_predict)
                S = S_
                reward += R

                path_.append(S)
                # print(q_table)
                # print(path_)
            # print("删除前\n path_list is {}\n path_ is {}".format(path_list,path_))
            path_list,path_ = self.dele_fun(path_list,path_)
            # print("删除后\n path_list is {}\n path_ is {}".format(path_list,path_))
            leiji_reward.append(reward)
            if self.EPSILON < self.MAX_EPSILON:
                self.EPSILON = self.EPSILON + self.EPSILON_increment
            else:
                self.EPSILON = self.MAX_EPSILON
            # print("第{}次最佳路径".format(path_))
            # print('训练{}次完成,EPSION是{}'.format(time + 1,self.EPSILON))
        q_table.to_excel("./table/q_table.xlsx", index=True)
        # print(q_table)
        shortest_list = min(path_list, key=len)
        return leiji_reward, step_s,path_list,shortest_list

    def dele_fun(self,path_list,path):
        # 删除path中重复的元素,使得path_list中的元素为不连续重复
        # 如 [7777755511155511155577]--------->[7515157]
        result = [x for i, x in enumerate(path) if i == 0 or x != path[i - 1]]
        path_list.append(result)
        return path_list, result

    def path_delay(self,step, path_list, delay):
        delay_list = []
        for i in step:
            delay_i = 0
            path_i = path_list[i]
            for curr, next in zip(path_i[:-1], path_i[1:]):
                # print('pathi = {}，curr is {}, next is {}'.format(path_i, curr, next))
                delay_i = delay.loc[curr, next] + delay_i
            delay_list.append(delay_i)
        return delay_list

    def path_loss(self,step, path_list, loss):
        loss_list = []
        for i in step:
            loss_i = 1
            path_i = path_list[i]
            for curr, next in zip(path_i[:-1], path_i[1:]):
                # print('pathi = {}，curr is {}, next is {}'.format(path_i, curr, next))
                loss_i = (1 - (loss.loc[curr, next]) / 100) * loss_i
            loss_i = abs(1 - loss_i)
            loss_list.append(loss_i)
        return loss_list

    def path_jitter(self,step, path_list, jitter):
        loss_jitter = []
        for i in step:
            jitter_i = 0
            path_i = path_list[i]
            for curr, next in zip(path_i[:-1], path_i[1:]):
                # print('pathi = {}，curr is {}, next is {}'.format(path_i, curr, next))
                jitter_i = jitter.loc[curr, next] + jitter_i
            # jitter_i = jitter_i/len(path_i)
            loss_jitter.append(jitter_i)
        return loss_jitter

    def test(self):
        print(self.reward_delay_room)






if __name__ == "__main__":
    reward_delay4 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew2.xlsx', header=0,
                                  index_col=0, sheet_name='delay')
    reward_loss4 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew2.xlsx', header=0,
                                 index_col=0, sheet_name='loss')
    reward_jitter4 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew2.xlsx', header=0,
                                   index_col=0, sheet_name='jitter')

    b = Q_LEARN(reward_delay4, reward_loss4, reward_jitter4,MAX_TIMES=300,
                EPSILON_increment=0.009, delay_ALPHA=0.25, loss_BETA=0.25, jitter_GAMMA=0.5)

    leiji_reward, step_s2, path_list2, shortest_list2 = b.rl(7, 20)




