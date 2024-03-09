# -*- coding:utf-8 -*-
"""
作者:${彭忠林}
日期:2023年10月12日
"""
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import random
from itertools import combinations
import q_learing
access_port = {5: set(), 2: set(), 17: set(), 15: {3}, 20: {3}, 19: {3}, 7: {3}, 6: set(), 1: set(), 18: set(), 13: set(), 4: set(), 3: set(), 10: set(), 14: set(), 8: {3}, 12: {3}, 9: set(), 16: {3}, 11: {3}}

access_table = {(7, 3): ('10.0.0.1', '00:00:00:00:00:01'), (8, 3): ('10.0.0.2', '00:00:00:00:00:02'), (11, 3): ('10.0.0.3', '00:00:00:00:00:03'), (12, 3): ('10.0.0.4', '00:00:00:00:00:04'), (15, 3): ('10.0.0.5', '00:00:00:00:00:05'), (16, 3): ('10.0.0.6', '00:00:00:00:00:06'), (19, 3): ('10.0.0.7', '00:00:00:00:00:07'), (20, 3): ('10.0.0.8', '00:00:00:00:00:08')}
ACTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
N_STATES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
q_table = pd.DataFrame(
        np.zeros((len(ACTIONS), len(N_STATES))),  # q_table为一个4x3的表格，并初始化值都为0
        columns=N_STATES,
        index=ACTIONS  # actions's name
    )  # 建立一个q表，且初始值都为0

def test():
    #没写完，先别删
    result = []

    # for key1, value1 in access_table.items():
    #     # print(key1,value1)
    #     for key2, value2 in access_table.items():
    #         if key1 != key2:
    #             result.append([(key1, value1), (key2, value2)])
    #
    #
    # for i in result:
    #     src = i[0][0][0]
    #     dst = i[1][0][0]
    #     src_port
    #     out_port
    #     print(src,dst)

# [(7, 3): ('10.0.0.1', '00:00:00:00:00:01'), (8, 3): ('10.0.0.2', '00:00:00:00:00:02'), (11, 3): ('10.0.0.3', '00:00:00:00:00:03'), (12, 3): ('10.0.0.4', '00:00:00:00:00:04'), (15, 3): ('10.0.0.5', '00:00:00:00:00:05'), (16, 3): ('10.0.0.6', '00:00:00:00:00:06'), (19, 3): ('10.0.0.7', '00:00:00:00:00:07'), (20, 3): ('10.0.0.8', '00:00:00:00:00:08')]
def path_delay(step, path_list, delay):
    delay_list = []
    for i in step:
        delay_i = 0
        path_i = path_list[i]
        for curr, next in zip(path_i[:-1], path_i[1:]):
                # print('pathi = {}，curr is {}, next is {}'.format(path_i, curr, next))
            delay_i = delay.loc[curr, next] + delay_i
        delay_list.append(delay_i)
        return delay_list
def hans():
    step = [0,1]
    path_list = [[7, 5, 1, 17, 20],[7, 5, 1, 17, 20,7, 5, 1, 17, 20]]
    reward_delay1 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew.xlsx', header=0,
                                  index_col=0, sheet_name='delay')
    print(reward_delay1)
    delay_list = []
    for i in step:
        delay_i = 0
        path_i = path_list[i]
        for curr, next in zip(path_i[:-1], path_i[1:]):
             # print('pathi = {}，curr is {}, next is {}'.format(path_i, curr, next))
            delay_i = reward_delay1.loc[curr, next] + delay_i
        delay_list.append(delay_i)
    print(delay_list)
    # delat = path_delay(0,path_list,reward_delay1)
    # print(delat)


def ceshi():
    k = 5
    reward_delay1 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew.xlsx', header=0,
                                  index_col=0, sheet_name='delay')
    reward_loss1 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew.xlsx', header=0,
                                 index_col=0, sheet_name='loss')
    reward_jitter1 = pd.read_excel('D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\rew.xlsx', header=0,
                                   index_col=0, sheet_name='jitter')
    b = q_learing.Q_LEARN(reward_delay1, reward_loss1, reward_jitter1, 0.0009, EPSILON_increment=0.008, MAX_TIMES=200)
    leiji_reward, step_s, path_list, shortest_list = b.rl(7, 20)
    delay_list = (b.path_delay(step_s, path_list, reward_delay1))
    loss_list = (b.path_loss(step_s, path_list, reward_loss1))
    jitter_list = (b.path_jitter(step_s, path_list, reward_loss1))

    # y = savgol_filter(delay_list, 21, 10, mode='nearest')
    y = []
    for i in range(len(delay_list)):
        start_index = max(0, i - k + 1)  # 计算当前窗口的起始索引
        end_index = min(i + 1, len(delay_list))  # 计算当前窗口的结束索引
        window = delay_list[start_index:end_index]  # 获取当前滑动窗口内的数据
        avg = sum(window) / len(window)  # 计算窗口内数据的平均值
        y.append(avg)
    b = q_learing.Q_LEARN(reward_delay1, reward_loss1, reward_jitter1, 0.009, EPSILON_increment=0.008, MAX_TIMES=200)
    leiji_reward2, step_s, path_list, shortest_list2 = b.rl(7, 20)
    delay_list2 = (b.path_delay(step_s, path_list, reward_delay1))
    loss_list2 = (b.path_loss(step_s, path_list, reward_loss1))
    jitter_list2 = (b.path_jitter(step_s, path_list, reward_loss1))
    # y2 = savgol_filter(delay_list, 21, 10, mode='nearest')
    y2 = []
    for i in range(len(delay_list2)):
        start_index = max(0, i - k + 1)  # 计算当前窗口的起始索引
        end_index = min(i + 1, len(delay_list2))  # 计算当前窗口的结束索引
        window = delay_list2[start_index:end_index]  # 获取当前滑动窗口内的数据
        avg = sum(window) / len(window)  # 计算窗口内数据的平均值
        y2.append(avg)

    b = q_learing.Q_LEARN(reward_delay1, reward_loss1, reward_jitter1, 0.09, EPSILON_increment=0.008, MAX_TIMES=200)
    leiji_reward3, step_s, path_list, shortest_list2 = b.rl(7, 20)
    delay_list3 = (b.path_delay(step_s, path_list, reward_delay1))
    loss_list2 = (b.path_loss(step_s, path_list, reward_loss1))
    jitter_list2 = (b.path_jitter(step_s, path_list, reward_loss1))
    # y2 = savgol_filter(delay_list, 21, 10, mode='nearest')
    y3 = []
    for i in range(len(delay_list3)):
        start_index = max(0, i - k + 1)  # 计算当前窗口的起始索引
        end_index = min(i + 1, len(delay_list3))  # 计算当前窗口的结束索引
        window = delay_list3[start_index:end_index]  # 获取当前滑动窗口内的数据
        avg = sum(window) / len(window)  # 计算窗口内数据的平均值
        y3.append(avg)

    b = q_learing.Q_LEARN(reward_delay1, reward_loss1, reward_jitter1, 0.9, EPSILON_increment=0.008, MAX_TIMES=200)
    leiji_reward4, step_s, path_list, shortest_list2 = b.rl(7, 20)
    delay_list4 = (b.path_delay(step_s, path_list, reward_delay1))
    loss_list2 = (b.path_loss(step_s, path_list, reward_loss1))
    jitter_list2 = (b.path_jitter(step_s, path_list, reward_loss1))
    # y2 = savgol_filter(delay_list, 21, 10, mode='nearest')
    y4 = []
    for i in range(len(delay_list4)):
        start_index = max(0, i - k + 1)  # 计算当前窗口的起始索引
        end_index = min(i + 1, len(delay_list4))  # 计算当前窗口的结束索引
        window = delay_list4[start_index:end_index]  # 获取当前滑动窗口内的数据
        avg = sum(window) / len(window)  # 计算窗口内数据的平均值
        y4.append(avg)

    # 画图
    plt.figure(1)
    # plt.plot(step_s, delay_list, alpha=0.6, color='lightblue')
    plt.plot(y, color='deepskyblue', label='learning_data={}'.format(0.0009))
    # plt.plot(step_s, delay_list2, alpha=0.6, color='pink')
    plt.plot(y2, color='deeppink', label='learning_data={}'.format(0.009))
    plt.plot(y3, color='lawngreen', label='learning_data={}'.format(0.09))
    plt.plot(y4, color='yellow', label='learning_data={}'.format(0.9))
    plt.xlabel('steps')
    plt.ylabel('latency')
    plt.legend()  # 显示标签
    plt.grid(True, linestyle='--', alpha=0.6)



    plt.figure(2)
    # plt.plot(step_s, delay_list, alpha=0.6, color='lightblue')
    plt.plot(leiji_reward, color='deepskyblue', label='learning_data={}'.format(0.0009))
    # plt.plot(step_s, delay_list2, alpha=0.6, color='pink')
    plt.plot(leiji_reward2, color='deeppink', label='learning_data={}'.format(0.009))
    plt.plot(leiji_reward3, color='lawngreen', label='learning_data={}'.format(0.09))
    plt.plot(leiji_reward4, color='yellow', label='learning_data={}'.format(0.9))
    plt.xlabel('steps')
    plt.ylabel('reward')
    plt.legend()  # 显示标签
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.show()

    # df = pd.DataFrame(y2)
    # # 保存到本地excel
    # df.to_excel("D:\\VMshare\\ryu-experiment\\experimen\\testdata\\reward\\y2.xlsx", index=False, startcol=1)


def sda():
    reward = [1,1,2,3,43,5,6,21,3]

    # for i in range(len(reward)):
    #     offset = random.randint(-10, 10)  # 生成-10到10之间的随机数
    #     reward[i] += offset

    print(reward)


if __name__ == "__main__":
    # [0.0009, 0.009, 0.09, 0.9]
    # scipy.signal.savgol_filter(x, window_length, polyorder)
    # [7, 5, 1, 17, 20 ] = 300ms
    """
    x为要滤波的信号
    window_length即窗口长度
    取值为奇数且不能超过len(x)。它越大，则平滑效果越明显；越小，则更贴近原始曲线。
    polyorder为多项式拟合的阶数。
    它越小，则平滑效果越明显；越大，则更贴近原始曲线。
    """
    # hans()

    ceshi()

    # sda()


