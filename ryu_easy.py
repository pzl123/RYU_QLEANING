# -*- coding:utf-8 -*-
"""
作者:${彭忠林}
日期:2023年07月07日
"""
# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : net_structure.py
# Data       ：3/30/23 8:01 PM
# Author     ：pzl
# version    ：python 3.8
# Description：
"""
import copy
import time
import networkx as nx
from operator import attrgetter
from ryu import cfg
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER,CONFIG_DISPATCHER,set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet,ethernet,ipv4,arp,igmp,ether_types
from ryu.lib import hub,igmplib,mac
from ryu.lib.dpid import str_to_dpid

from ryu.topology.switches import LLDPPacket
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link,get_host


import pandas as pd
import numpy as np


#导入强化学习部分f
import q_learing
import datetime


import copy


# Common Setting for Networ awareness module.
DISCOVERY_PERIOD = 10  # For discovering topology.
MONITOR_PERIOD = 10  # For monitoring traffic
DELAY_DETECTING_PERIOD = 5  # For detecting link delay.
TOSHOW = True  # For showing information in terminal
MAX_CAPACITY = 281474976710655  # Max capacity of link
SCHEDULE_PERIOD = 6  # shortest forwarding network awareness period
hard_timeout = 65535 #存活时间，如值为 10，则从该流表被安装经过 10s 后无论被使用情况如何，立即被删除

class NetworkAwareness(app_manager.RyuApp):
    """
        NetworkAwareness is a Ryu app for discover topology information.
        This App can provide many data services for other App, such as
        link_to_port, access_table, switch_port_table,access_ports,
        interior_ports,topology graph and shorteest paths.

    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # List the event list should be listened.
    events = [event.EventSwitchEnter,
              event.EventSwitchLeave, event.EventPortAdd,
              event.EventPortDelete, event.EventPortModify,
              event.EventLinkAdd, event.EventLinkDelete]
    N = 1

    def __init__(self, *args, **kwargs):
        super(NetworkAwareness, self).__init__(*args, **kwargs)
        #topo发现部分
        self.topology_api_app = self
        self.name = "structure_awarness"
        self.graph = nx.DiGraph()
        self.link_to_port = {} #{(src.dpid, dst.dpid):(src.port_no, dst.port_no)}
        self.switch_port_table = {}  # {dpid:port} 所有的dpid及其port 等同于self.switch_all_ports_table
        self.interior_ports = {}  # {dpid:port} 所有的交换机之间的dpid及其port  等同于structure中的self.switch_port_table
        self.access_ports = {}   # {dpid:port} 所有的交换机与主机之间的dpid及其port   {5: set(), 2: set(), 17: set(), 15: {3}, 20: {3}, 19: {3}, 7: {3}, 6: set(), 1: set(),
        # self.access_table = {} # 主机与交换机连接情况 等同于 self.not_use_ports
        self.access_table = {} #access_table is [(dpid, in_port)] = (ip, mac)  所有链接的host信息 {(7, 3): ('10.0.0.1', '00:00:00:00:00:01'), (8, 3): ('10.0.0.2', '00:00:00:00:00:02'),
        self.datapaths = {} # arp使用 {dpid:datapath}
        self.discover_thread = hub.spawn(self._discover)




        #网络监控部分
        self.port_flow_dpid_stats = {'port': {}, 'flow': {}}  # {'port': {dpid:body}, 'flow': {}} body:包含流的所有信息
        self.dpid_port_fueatures_table = {}  # {dpid:{port_no: (config, state, curr_speed, max_speed)}}
        self.flow_stats_table = {}  # {dpid:{(in_port, ipv4_dsts, out_port): (packet_count, byte_count, duration_sec, duration_nsec)}}
        self.port_stats_table = {}  # {(dpid, port_no):[(tx_bytes,rx_bytes,rx_errors,duration_sec,duration_nsec,tx_packets,rx_packets)]}
        self.port_speed_table = {}  # {(dpid, port_no):speed}
        self.port_loss = {}  # {(src_dpid,dst_dpid): loss_ratio}  loss_ratio = abs(float(tx - rx) / tx) * 100, 存储5次
        self.link_port_table = {}  # {(src.dpid, dst.dpid): (src.port_no, dst.port_no)}

        self.free_bandwidth ={} # {dpid:{port:curr_bw MBit/s} curr_bw = max(curr_speed/10**3-(now_bytes - pre_bytes)/delta_time*8/10**6, 0)

        self.path = []

        self.delay_path = []
        self.loss_path = []
        self.bw_path = []


        #时延部分
        self.net_delay = lookup_service_brick('net_delay')


        #数据处理部分
        self.ACTIONS = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]

        self.N_STATES = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
        self.reward_loss_room = pd.DataFrame(
            np.zeros((len(self.ACTIONS), len(self.N_STATES))),  # q_table为一个4x3的表格，并初始化值都为0
            columns=self.N_STATES,
            index=self.ACTIONS # actions's name
        )
        self.reward_delay_room = pd.DataFrame(
            np.zeros((len(self.ACTIONS), len(self.N_STATES))),  # q_table为一个4x3的表格，并初始化值都为0
            columns=self.N_STATES,
            index=self.ACTIONS # actions's name
        )
        self.reward_jitter_room = pd.DataFrame(
            np.zeros((len(self.ACTIONS), len(self.N_STATES))),  # q_table为一个4x3的表格，并初始化值都为0
            columns=self.N_STATES,
            index=self.ACTIONS # actions's name
        )


        #强化学习部分
        self.a = q_learing.Q_LEARN(delay=self.reward_delay_room, loss=self.reward_loss_room,
                                 jitter=self.reward_jitter_room,
                                 ACTIONS=self.ACTIONS, N_STATES=self.N_STATES)



        self.monitor_thread = hub.spawn(self.scheduler)
        self.monitor_thread = hub.spawn(self.measurement)



    def _discover(self):
        print('开始登记')
        i = 0
        delay_list = [0, 1, 2]
        loss_list = [0, 1, 2]
        while True:
            self.get_topology(None)
            self.ACTIONS = list(self.graph.nodes)
            self.ACTIONS.sort()
            self.N_STATES = self.ACTIONS
            # print(self.ACTIONS)
            if len(self.ACTIONS)!=0:
                delay, loss = self.link_data(self.ACTIONS,self.N_STATES)
                loss[loss > 100] = 0
                if i == 0:
                    delay_list[0] = copy.deepcopy(delay)
                    loss_list[0] = copy.deepcopy(loss)
                elif i == 1:
                    delay_list[1] = copy.deepcopy(delay)
                    loss_list[1] = copy.deepcopy(loss)
                elif i == 2:
                    delay_list[2] = copy.deepcopy(delay)
                    loss_list[2] = copy.deepcopy(loss)
                self.reward_delay_room, self.reward_loss_room, self.reward_jitter_room = delay, loss, self.huode_jitter(
                    delay_list)
                i = i + 1
                if i > 2:
                    i = 0
            hub.sleep(5)

    def scheduler(self):
        while True:
            self.port_flow_dpid_stats['flow'] = {}
            self.port_flow_dpid_stats['port'] = {}
            datapaths_table = self.datapaths.values()
            for datapath in list(datapaths_table):
                self.dpid_port_fueatures_table.setdefault(datapath.id, {})
                self._request_stats(datapath)
            # self.create_bandwidth_graph()
            self.create_loss_graph()
            hub.sleep(1)
            # print("test for time_reward \n{}\n".format(self.reward_delay_room))

    def measurement(self):
        hub.sleep(30)
        while True:
            # print(self.reward_delay_room)
            if self.reward_loss_room.isnull().values.any() or self.reward_jitter_room.isnull().values.any() or self.reward_delay_room.isnull().values.any():
                self.reward_loss_room = pd.DataFrame(np.zeros((len(self.ACTIONS), len(self.N_STATES))),columns=self.ACTIONS,index=self.N_STATES)

                self.reward_jitter_room = pd.DataFrame(np.zeros((len(self.ACTIONS), len(self.N_STATES))),columns=self.ACTIONS,index=self.N_STATES)

                self.reward_delay_room = pd.DataFrame(np.zeros((len(self.ACTIONS), len(self.N_STATES))),columns=self.ACTIONS, index=self.N_STATES)

            self.a = q_learing.Q_LEARN(delay=self.reward_delay_room, loss=self.reward_loss_room,
                                       jitter=self.reward_jitter_room,MAX_TIMES=60,
                                       ACTIONS=self.ACTIONS, N_STATES=self.N_STATES)
            if self.a.reward_room_data.isna().values.any():
                self.a.reward_room_data = pd.read_excel('reward_room.xlsx')


            print("test rl in measurement\n")
            leiji_reward, step_s2, path_list2, shortest_list2 = self.a.rl(7,20)
            # ql_delay = self.a.path_delay(step_s2, path_list2, self.reward_delay_room)
            # ql_loss = self.a.path_loss(step_s2, path_list2, self.reward_loss_room)
            # ql_jitter = self.a.path_loss(step_s2, path_list2, self.reward_jitter_room)
            # s_delay = 0
            # s_loss = 0
            # s_jitter = 0
            # for curr, next in zip(path1[:-1], path1[1:]):
            #     s_delay = float((self.reward_delay_room.loc[[curr], [next]]).values) + s_delay
            #     s_loss = float((self.reward_loss_room.loc[[curr], [next]]).values) + s_loss
            #     s_jitter = float((self.reward_jitter_room.loc[[curr], [next]]).values) + s_jitter
            # print("shortest delay is {}\n".format(s_delay))
            # print("shortest loss is {}\n".format(s_loss))
            # print("shortest jitter is {}\n".format(s_jitter))
            # print("ql delay is {}\n".format(min(ql_delay)))
            # print("ql loss is {}\n".format(min(ql_loss)))
            # print("ql jitter is {}\n".format(min(ql_jitter)))
            # 获取当前日期和时间
            # current_datetime = datetime.datetime.now()
            # # 格式化日期和时间为字符串
            # current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            # delay = 0
            # with open('myfile.txt', 'a') as file:
            #     # 写入内容
            #     file.write('{}\n'
            #                's_delay is {}\n'
            #                's_loss is {}\n'
            #                's_jitter is {}\n'
            #                'ql_delay is {}\n'
            #                'ql_loss is {}\n'
            #                'ql_jitter is {}\n\n'.format(current_datetime_str, s_delay,s_loss,s_jitter,min(ql_delay),min(ql_loss),min(ql_jitter)))
            # file.close()
            #
            hub.sleep(10)



    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """ 存放所有的datapath实例"""
        datapath = ev.datapath  # OFPStateChange类可以直接获得datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                # print("MMMM--->  register datapath: %016x" % datapath.id)
                self.datapaths[datapath.id] = datapath
                self.dpid_port_fueatures_table.setdefault(datapath.id, {})
                self.flow_stats_table.setdefault(datapath.id, {})
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                # print("MMMM--->  unreigster datapath: %016x" % datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
            Initial operation, send miss-table flow entry to datapaths.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        msg = ev.msg
        # self.logger.info("switch:%s connected", datapath.id)

        dpid = datapath.id
        self.datapaths[dpid] = datapath

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, dp, priority, match, actions, hard_timeout=hard_timeout):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=priority,
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
            Hanle the packet in packet, and register the access info.
        """

        msg = ev.msg
        datapath = msg.datapath

        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        # print('in_port is {}'.format(in_port))
        pkt = packet.Packet(msg.data)

        eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if eth_type == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        if ip_pkt:
            src_ipv4 = ip_pkt.src
            src_mac = eth_pkt.src
            if src_ipv4 != '0.0.0.0' and src_ipv4 != '255.255.255.255':
                # print("ip_pkt")
                self.register_access_info(datapath.id, in_port, src_ipv4, src_mac)

        if arp_pkt:
            arp_src_ip = arp_pkt.src_ip
            arp_dst_ip = arp_pkt.dst_ip
            mac = arp_pkt.src_mac
            # Record the access info
            self.register_access_info(datapath.id, in_port, arp_src_ip, mac)


        if isinstance(arp_pkt, arp.arp):#如果arp_pkt属于arp.arp类型
            self.arp_forwarding(msg, arp_pkt.src_ip, arp_pkt.dst_ip)

        if isinstance(ip_pkt, ipv4.ipv4):  # 如果ip_pkt属于ipv4类型
            if len(pkt.get_protocols(ethernet.ethernet)):
                result = self.get_sw(datapath.id, in_port, ip_pkt.src, ip_pkt.dst)
                if result:
                    src_sw, dst_sw, to_dst_port = result[0], result[1], result[2]
                    if dst_sw:
                        # print(src_sw,dst_sw)
                        to_dst_match = parser.OFPMatch(eth_type=eth_type, ipv4_dst=ip_pkt.dst)
                        port_no = self.set_shortest_path(src_sw, dst_sw, to_dst_port,to_dst_match)
                        self.send_packet_out(datapath, msg.buffer_id, in_port, port_no, msg.data)
        return

    def get_topology(self, ev):
        """
        Get topology info and calculate shortest paths.
        """
        for sw in get_switch(self.topology_api_app, None):
            self.graph.add_node(sw.dp.id)
            # self.dps[sw.dp.id] = sw.dp
            #初始化字典
            self.switch_port_table.setdefault(sw.dp.id, set())
            self.interior_ports.setdefault(sw.dp.id, set())
            self.access_ports.setdefault(sw.dp.id, set())
            for p in sw.ports:
                self.switch_port_table[sw.dp.id].add(p.port_no)

        for link in get_link(self.topology_api_app, None):
            src = link.src
            dst = link.dst
            weight = 0
            self.graph.add_edge(src.dpid, dst.dpid,
                                src_port=src.port_no,dst_port=dst.port_no,
                                weight=weight+0.001)
            self.link_to_port[(src.dpid, dst.dpid)] = (src.port_no, dst.port_no)

            # Find the access ports and interiorior ports
            if link.src.dpid in self.switch_port_table.keys():
                self.interior_ports[link.src.dpid].add(link.src.port_no)
            if link.dst.dpid in self.switch_port_table.keys():
                self.interior_ports[link.dst.dpid].add(link.dst.port_no)
            # 存入交换机之间连接的端口

        for sw in self.switch_port_table:
            self.access_ports[sw] = self.switch_port_table[sw] - self.interior_ports[sw]

        # print(self.graph.get_edge_data(1,5))

    def k_shortest_paths(self, graph, src, dst, weight, k=3):
        """
            Great K shortest paths of src to dst.
        """
        generator = nx.shortest_simple_paths(graph, source=src,target=dst, weight=weight)
        shortest_paths = []
        try:
            for path in generator:
                if k <= 0:
                    break
                shortest_paths.append(path)
                k -= 1
            return shortest_paths
        except:
            self.logger.debug("No path between %s and %s" % (src, dst))

    def get_host_location(self, host_ip):
        """
            Get host location info:(datapath, port) according to host ip.
            根据主机 ip 获取主机位置信息：（数据路径、端口）
            key is (dpid, in_port) {(7, 3): ('10.0.0.1', '00:00:00:00:00:01'),}
            返回的时 dst_dpid 与 port 主机相连的端口
        """
        for key in self.access_table.keys():
            if self.access_table[key][0] == host_ip:
                return key
        return None

    def get_sw(self, dpid, in_port, src, dst):
        """
            Get pair of source and destination switches.
            传入 datapath.id, in_port, ip_pkt.src, ip_pkt.dst

                datapath.id is 20
                in_port is 3
                in_pkt.src is 10.0.0.8
                in_pkt.dst is is 10.0.0.7

            返回 src_sw, dst_sw, dst_port

                src_sw is 20
                dst_sw is 19
                to_dst_port is 3

        """
        # print("-----Get pair of source and destination switches------")
        src_sw = dpid
        dst_sw = None
        dst_port = None

        src_location = self.get_host_location(src) # 返回的是主机与交换机连接的信息(dpid,port)
        if in_port in self.access_ports[dpid]:
            if (dpid,  in_port) == src_location:
                src_sw = src_location[0]#src_location[0]是dpid
            else:
                return None

        dst_location = self.get_host_location(dst)
        if dst_location:
            dst_sw = dst_location[0]
            dst_port = dst_location[1]
        return src_sw, dst_sw, dst_port

    def register_access_info(self, dpid, in_port, ip, mac):
        """
            Register access host info into access table.
        """
        # print("register " + ip)
        # if in_port in self.access_ports[dpid]:
        #     if (dpid, in_port) in self.access_table:
        #         if self.access_table[(dpid, in_port)] == (ip, mac):
        #             return
        #         else:
        #             self.access_table[(dpid, in_port)] = (ip, mac)
        #             return
        #     else:
        #         self.access_table.setdefault((dpid, in_port), None)
        #         self.access_table[(dpid, in_port)] = (ip, mac)
        #         return

        if dpid in self.access_ports:
            if in_port in self.access_ports[dpid]:
                if (dpid, in_port) in self.access_table:
                    if self.access_table[(dpid, in_port)] == (ip, mac):
                        return
                    else:
                        self.access_table[(dpid, in_port)] = (ip, mac)
                        return
                else:
                    self.access_table.setdefault((dpid, in_port), None)
                    self.access_table[(dpid, in_port)] = (ip, mac)
                    return
            else:# 处理in_port不存在于access_ports[dpid]的情况
                self.access_ports.setdefault(dpid, in_port)
                # print("in_port not in access_ports")
                return


        else: # 处理dpid不存在于access_ports的情况
            self.access_ports.setdefault(dpid, set())
            # print("dpip not in access_port")
            return


    def arp_forwarding(self, msg, src_ip, dst_ip):
        """ Send ARP packet to the destination host,
            if the dst host record is existed,
            else, flow it to the unknow access port.
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        result = self.get_host_location(dst_ip)
        if result:  # host record in access table.
            datapath_dst, out_port = result[0], result[1]
            datapath = self.datapaths[datapath_dst]
            out = self._build_packet_out(datapath, ofproto.OFP_NO_BUFFER,
                                         ofproto.OFPP_CONTROLLER,
                                         out_port, msg.data)
            # print(out)
            datapath.send_msg(out)
        else:
            self.flood(msg)
    def _build_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Build packet out object.
        """
        actions = []
        if dst_port:
            actions.append(datapath.ofproto_parser.OFPActionOutput(dst_port))

        msg_data = None
        if buffer_id == datapath.ofproto.OFP_NO_BUFFER:
            if data is None:
                return None
            msg_data = data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=buffer_id,
            data=msg_data, in_port=src_port, actions=actions)
        return out

    def flood(self, msg):
        """
            Flood ARP packet to the access port
            which has no record of host.
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dpid in self.access_ports:
            for port in self.access_ports[dpid]:
                if (dpid, port) not in self.access_table.keys():
                    datapath = self.datapaths[dpid]
                    out = self._build_packet_out(
                        datapath, ofproto.OFP_NO_BUFFER,
                        ofproto.OFPP_CONTROLLER, port, msg.data)
                    datapath.send_msg(out)

    def send_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Send packet out packet to assigned datapath.
        """
        out = self._build_packet_out(datapath, buffer_id,
                                     src_port, dst_port, data)
        if out:
            datapath.send_msg(out)

    def get_datapath(self, dpid):
        # 如果dpid表示的交换机不在self.datapaths {dpid:datapath} 则加入
        # 如果在 则直接返回 datapath 详细信息
        """
        例如  self.datapaths[dpid 3] is <ryu.controller.controller.Datapath object at 0x7f5a02f87850>
        """

        if dpid not in self.datapaths:#交换机不在列表的话
            switch = get_switch(self, dpid)[0]
            self.datapaths[dpid] = switch.dp#加入列表
            return switch.dp#返回该交换机的id,datapath
        # print('self.datapaths[dpid {}] is {}'.format(dpid,self.datapaths[dpid]))
        return self.datapaths[dpid]#在的话直接返回交换机id,datapath




    def set_shortest_path(self,src_dpid,dst_dpid,to_port_no,to_dst_match,pre_actions=[]):
        """
        传入 源dpid 目的dpid 目的端口  匹配项
        输出
        """

        if nx.has_path(self.graph, src_dpid, dst_dpid):#存在路径?
            # leiji_reward, step_s2, path_list2, shortest_list2= self.a.rl(src_dpid,dst_dpid)
            # ql_delay = self.a.path_delay(step_s2, path_list2, self.reward_delay_room)
            # # ql_loss = self.a.path_loss(step_s2, path_list2, self.reward_loss_room)
            # # ql_jitter = self.a.path_loss(step_s2, path_list2, self.reward_jitter_room)
            # path2 = path_list2[ql_delay.index(min(ql_delay))]
            # print("ql_path is {}".format(path2))

            # s_delay = 0
            path1 = self.k_shortest_paths(self.graph, src_dpid, dst_dpid, weight="weight")[0]  # path返回的是列表 path=[1,2,3,4]
            # print("s_path is {}".format(path1))
            # for curr, next in zip(path1[:-1], path1[1:]):
            #     s_delay = float((self.reward_delay_room.loc[[curr], [next]]).values) + s_delay
            #
            #
            # print("compare s_delay{} and ql_delay{} ".format(s_delay,min(ql_delay)))
            # if(len(path1)==len(path2)):
            #     path = path2
            # else:
            #     path = path1
            # print(path)
            path = path1
        else:
            path = None
        if path is None:
            self.logger.info("Get path failed.")
            return 0

        if len(path) == 1:#直连
            dp = self.get_datapath(src_dpid) # 返回的是datapath 不是dpid,是改交换机的详细信息 如 <ryu.controller.controller.Datapath object at 0x7f5a02f87610>
            actions = [dp.ofproto_parser.OFPActionOutput(to_port_no)]
            self.add_flow(dp, 10, to_dst_match, pre_actions+actions, hard_timeout=hard_timeout)
            port_no = to_port_no
            # print("path = 1 port_no is to_port_no{}".format(to_port_no))
        else:
            self.install_path(to_dst_match, path, pre_actions)# 安装路径流表
            dst_datapath = self.get_datapath(dst_dpid)# 得到目的交换机的id,datapath
            actions = [dst_datapath.ofproto_parser.OFPActionOutput(to_port_no)]
            self.add_flow(dst_datapath, 10, to_dst_match, pre_actions+actions,hard_timeout=hard_timeout)
            port_no = self.graph[path[0]][path[1]]['src_port']

        return port_no

    def install_path(self, match, path, pre_actions=[]):#path=[a,b,c,d,e,f,g] 字母为dpid
        for index, dpid in enumerate(path[:-1]):
            port_no = self.graph[path[index]][path[index + 1]]['src_port']#获取转发端口
            dp = self.get_datapath(dpid)
            actions = [dp.ofproto_parser.OFPActionOutput(port_no)]
            self.add_flow(dp, 10, match, pre_actions+actions, hard_timeout=hard_timeout) #添加到流表内





    # 网络监控部分
    def _request_stats(self, datapath):
        # print("MMMM--->  send request --->   ---> send request ---> ")
        # datapaths_table = self.datapaths_table.values()
        # for datapath in list(datapaths_table):
        #     self.dpid_port_fueatures_table.setdefault(datapath.id, {})
        # print("MMMM--->  send stats request: %016x", datapath.id)

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # 1. 端口描述请求
        req = parser.OFPPortDescStatsRequest(datapath, 0)
        datapath.send_msg(req)

        # 2. 端口统计请求
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)  # 所有端口
        datapath.send_msg(req)

        # 3. 单个流统计请求
        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

    # 处理上面请求的回复OFPPortDescStatsReply
    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        """ 存储端口描述信息, 见OFPPort类, 配置、状态、当前速度"""
        # print("MMMM--->  EventOFPPortDescStatsReply")
        # print(self.datapaths_table)
        msg = ev.msg
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        config_dict = {ofproto.OFPPC_PORT_DOWN: 'Port Down',
                       ofproto.OFPPC_NO_RECV: 'No Recv',
                       ofproto.OFPPC_NO_FWD: 'No Forward',
                       ofproto.OFPPC_NO_PACKET_IN: 'No Pakcet-In'}

        state_dict = {ofproto.OFPPS_LINK_DOWN: "Link Down",
                      ofproto.OFPPS_BLOCKED: "Blocked",
                      ofproto.OFPPS_LIVE: "Live"}

        for ofport in ev.msg.body:  # 这一直有bug，修改properties
            if ofport.port_no != ofproto_v1_3.OFPP_LOCAL:  # 0xfffffffe  4294967294

                if ofport.config in config_dict:
                    config = config_dict[ofport.config]
                else:
                    config = 'Up'

                if ofport.state in state_dict:
                    state = state_dict[ofport.state]
                else:
                    state = 'Up'

                # 存储配置，状态, curr_speed
                port_features = (config, state, ofport.curr_speed)
                # print("==========port_features=============")
                # print("port_features:{}".format(port_features))
                # print("MMMM--->  ofport.curr_speed", ofport.curr_speed)
                self.dpid_port_fueatures_table[dpid][ofport.port_no] = port_features
                # print("==========dpid_port_fueatures_table=============")
                # print(self.dpid_port_fueatures_table)
                # print("")

        # print("MMMM--->  ofport.curr_speed", ofport.curr_speed)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_table_reply_handler(self, ev):
        """ 存储端口统计信息, 见OFPPortStats, 发送bytes、接收bytes、生效时间duration_sec等
         Replay message content:
        body=(stat.port_no,
             stat.rx_packets:Number of received packets, stat.tx_packets:Number of transmitted packets,
             stat.rx_bytes:Number of received bytes, stat.tx_bytes:Number of transmitted bytes,
             stat.rx_dropped:Number of packets dropped by RX, stat.tx_dropped:Number of packets dropped by TX,
             stat.rx_errors, stat.tx_errors,
             stat.rx_frame_err, stat.rx_over_err,
             stat.rx_crc_err, stat.collisions,
             stat.duration_sec, stat.duration_nsec))
        """
        # print("MMMM--->  EventOFPPortStatsReply")
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.port_flow_dpid_stats['port'][dpid] = body
        self.free_bandwidth.setdefault(dpid, {})
        # self.port_curr_speed.setdefault(dpid, {})
        # print(self.port_flow_dpid_stats['port'][dpid])

        for stat in sorted(body, key=attrgetter("port_no")):
            port_no = stat.port_no
            if port_no != ofproto_v1_3.OFPP_LOCAL:  # 0xfffffffe  Local openflow "port".
                key = (dpid, port_no)
                value = (stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                         stat.duration_sec, stat.duration_nsec, stat.tx_packets, stat.rx_packets)
                self._save_stats(self.port_stats_table, key, value, 5)  # 保存信息，最多保存前5次

                # print("==================stat in dpid{} start：====================".format(dpid))
                # print(stat.rx_dropped,stat.tx_dropped)
                # print("stat.tx_bytes:{}\n "
                #       "stat.rx_bytes:{}\n "
                #       "stat.rx_errors:{}\n"
                #       "stat.duration_sec:{}\n"
                #       "stat.duration_nsec{}\n"
                #       "stat.tx_packets:{}\n"
                #       "stat.rx_packets：{}\n".format(stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                #          stat.duration_sec, stat.duration_nsec, stat.tx_packets, stat.rx_packets))
                # print("==================stat in dpid{} end：====================".format(dpid))

                pre_bytes = 0
                delta_time = SCHEDULE_PERIOD
                stats = self.port_stats_table[key]  # 获得已经存了的统计信息
                if len(stats) > 1:  # 有两次以上的信息
                    pre_bytes = stats[-2][0] + stats[-2][1]
                    delta_time = (stats[-1][3] + stats[-1][4] / 10 ** 9) - (stats[-2][3] + stats[-2][4] / 10 ** 9)# 3:stat.duration_sec,4: stat.duration_nsec 倒数第一个统计信息，倒数第二个统计信息
                    # print("delta_time is {}".format(delta_time))
                speed = self._calculate_speed(stats[-1][0] + stats[-1][1],# stat.tx_bytes, stat.rx_bytes
                                              pre_bytes, delta_time)
                # print("speed is {}".format(speed))
                self._save_stats(self.port_speed_table, key, speed, 5)
                # print("dpid port {} port_speed_table :{}".format(key,self.port_speed_table))
                # print("")
                # self._calculate_port_speed(dpid, port_no, speed)

                self._save_freebandwidth(dpid, port_no, speed)


        # self.calculate_loss_of_link()

    """
    存多次数据，比如一个端口存上一次的统计信息和这一次的统计信息
    存放的是端口body，存放数量是keep
                 stat.rx_packets, stat.tx_packets,
                 stat.rx_bytes, stat.tx_bytes,
                 stat.rx_dropped, stat.tx_dropped,
                 stat.rx_errors, stat.tx_errors,
                 stat.rx_frame_err, stat.rx_over_err,
                 stat.rx_crc_err, stat.collisions,
                 stat.duration_sec, stat.duration_nsec)
    """
    @staticmethod
    def _save_stats(_dict, key, value, keep):
        if key not in _dict:
            _dict[key] = []
        _dict[key].append(value)

        if len(_dict[key]) > keep:
            _dict[key].pop(0)  # 弹出最早的数据

    #
    # @staticmethod
    # def _calculate_seconds(sec, nsec):
    #     """ 计算 sec + nsec 的和，单位为 seconds"""
    #     return sec + nsec / 10 ** 9

    @staticmethod
    def _calculate_speed(now_bytes, pre_bytes, delta_time):
        """ 计算统计流量速度"""
        if delta_time:
            return (now_bytes - pre_bytes) / delta_time
        else:
            return 0

    # 下面为假
    def _calculate_port_speed(self, dpid, port_no, speed):
        # Calculate free bandwidth of port and save it.计算端口的可用带宽并保存。
        port_state = self.dpid_port_fueatures_table.get(dpid).get(port_no)
        if port_state:
            capacity = port_state[2]
            curr_bw = max(capacity/10**3 - speed * 8/10**6, 0)
        # curr_bw = speed * 8 / 10 ** 6  # MBit/s
        # print(f"monitorMMMM---> _calculate_port_speed: {curr_bw} MBits/s", )
        self.free_bandwidth.setdefault(dpid, {})
        self.free_bandwidth[dpid][port_no] = curr_bw

    def _save_freebandwidth(self, dpid, port_no, speed):
        # Calculate free bandwidth of port and save it.计算端口的可用带宽并保存。
        port_state = self.dpid_port_fueatures_table.get(dpid).get(port_no)
        if port_state:
            capacity = port_state[2]
            curr_bw = max(capacity/10**3 - speed * 8/10**6, 0)
            self.free_bandwidth[dpid].setdefault(port_no, None)
            # self.free_bandwidth.setdefault(dpid, {})
            self.free_bandwidth[dpid][port_no] = curr_bw
            # print("_save_freebandwidth is {}".format(curr_bw))



    # 通过获得的网络拓扑，更新其bw权重
    def create_bandwidth_graph(self):
        # print("MMMM--->  create bandwidth graph")
        try:
            # print(self.free_bandwidth)
            for link in self.link_to_port:
                src_dpid, dst_dpid = link
                src_port, dst_port = self.link_to_port[link]

                if src_dpid in self.free_bandwidth.keys() and dst_dpid in self.free_bandwidth.keys():
                    src_port_bw = self.free_bandwidth[src_dpid][src_port]
                    dst_port_bw = self.free_bandwidth[dst_dpid][dst_port]
                    src_dst_bandwidth = min(src_port_bw, dst_port_bw)  # bottleneck bandwidth 瓶颈带宽

                    # add key:value of bandwidth into graph.
                    self.graph[src_dpid][dst_dpid]['bw'] = src_dst_bandwidth
                    # print("src_dpid {} dst_dpid {} bw{}".format(src_dpid,dst_dpid,self.graph[src_dpid][dst_dpid]['bw']))

                else:
                    self.graph[src_dpid][dst_dpid]['bw'] = 0
        except:
            self.logger.info("Create bw graph exception")
            return self.graph


    # loss
    def calculate_loss_of_link(self):
        """
            calculate loss  rx1_packet - rx2_packet/ tx1_packet - tx2_packet
            发端口 和 收端口 ，端口loss
            stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
            stat.duration_sec, stat.duration_nsec,
            stat.tx_packets, stat.rx_packets,
            stat.tx_dropped,stat.rx_dropped
        """
        for link, port in self.link_to_port.items():
            src_dpid, dst_dpid = link
            src_port, dst_port = port
            if (src_dpid, src_port) in self.port_stats_table.keys() and \
                    (dst_dpid, dst_port) in self.port_stats_table.keys():

                tx = self.port_stats_table[(src_dpid, src_port)][-1][-2]
                rx = self.port_stats_table[(dst_dpid, dst_port)][-1][-1]
                loss_ratio = abs(tx - rx)/tx * 100
                if loss_ratio>=100:
                    loss_ratio = 0
                self._save_stats(self.port_loss, link, loss_ratio, 5)

                tx = self.port_stats_table[(dst_dpid, dst_port)][-1][-2]
                rx = self.port_stats_table[(src_dpid, src_port)][-1][-1]
                loss_ratio = abs(tx - rx) / tx * 100
                if loss_ratio >= 100:
                    loss_ratio = 0
                self._save_stats(self.port_loss, link, loss_ratio, 5)

                # print(f"MMMM--->[{link[::-1]}]({dst_dpid}, {dst_port}) rx: ", rx, "tx: ", tx,
                #       "loss_ratio: ", loss_ratio)
                # print(self.port_loss)
            else:
                self.logger.info("MMMM--->  calculate_loss_of_link error")

    # update graph loss
    def update_graph_loss(self):
        """从1 往2 和 从2 往1，取最大作为链路loss """
        for link in self.link_to_port:
            src_dpid = link[0]
            dst_dpid = link[1]
            if link in self.port_loss.keys() and link[::-1] in self.port_loss.keys():
                src_loss = self.port_loss[link][-1]  # 1-->2  -1取最新的那个
                dst_loss = self.port_loss[link[::-1]][-1]  # 2-->1
                link_loss = max(src_loss, dst_loss)  # 百分比 max loss between port1 and port2
                self.graph[src_dpid][dst_dpid]['loss'] = link_loss

                # print(f"MMMM---> update_graph_loss link[{link}]_loss: ", link_loss)
            else:
                self.graph[src_dpid][dst_dpid]['loss'] = 0

    def create_loss_graph(self):
        """
            在graph中更新边的loss值
        """
        self.calculate_loss_of_link()
        self.update_graph_loss()

    def link_data(self,ACTIONS,N_STATES):
        table = pd.DataFrame(
            np.zeros((len(ACTIONS), len(N_STATES))),
            columns=ACTIONS,
            index=N_STATES)
        # print(table)
        reward_loss_room = table.copy()
        reward_delay_room = table.copy()

        for link, port in self.link_to_port.items():
            src_dpid, dst_dpid = link
            # src_port, dst_port = port
            reward_loss_room.loc[src_dpid, dst_dpid] = self.graph[src_dpid].get(dst_dpid).get('loss')
            # print("loss in src{} and dst{} is :{}\n".format(src_dpid, dst_dpid,self.graph[src_dpid].get(dst_dpid).get('loss')))
            reward_delay_room.loc[src_dpid, dst_dpid] = self.graph[src_dpid].get(dst_dpid).get('delay')
            # print("delay in src{} and dst{} is :{}\n".format(src_dpid, dst_dpid,self.graph[src_dpid].get(dst_dpid).get('delay')))

        reward_loss_room[reward_loss_room > 100] = 0
        # print("delay in link_data is \n{}".format(reward_delay_room))
        # print("delay in link_data is {}\n\n".format(reward_delay_room))
        # print("loss in link_data is {}\n\n\n\n\n".format(reward_loss_room))


        return reward_delay_room, reward_loss_room

    def Calculate_the_loss_factor(self,loss_list):
        loss_ = pd.DataFrame(np.zeros((len(self.N_STATES), len(self.ACTIONS))),
                             columns=self.N_STATES,
                             index=self.ACTIONS)
        min_ls = pd.DataFrame(np.zeros((len(self.N_STATES), len(self.ACTIONS))),
                              columns=self.N_STATES,
                              index=self.ACTIONS)
        for loss in loss_list:
            loss_ += loss
        loss_ = loss_ / len(loss_list)
        for i in range(len(loss_list)):
            min_ls = (np.square(loss_list[i] - loss_)) / len(loss_list) + min_ls
        # print(min_ls)
        min_ls = np.sqrt(min_ls)
        return min_ls

    def Fill_the_reward_room(self, delay, loss,delay_list):
        # reward_delay_room = pd.DataFrame(np.mean(delay_list, axis=0), columns=self.ACTIONS, index=self.N_STATES)
        # reward_loss_room = pd.DataFrame(np.mean(loss_list, axis=0), columns=self.ACTIONS, index=self.N_STATES)
        # reward_jitter_room = self.huode_jitter(delay_list)
        reward_delay_room = delay_list
        reward_loss_room = loss
        reward_jitter_room = self.huode_jitter(delay_list)
        return reward_delay_room, reward_loss_room, reward_jitter_room

    def huode_jitter(self, delay_list):
        max_jitter1 = abs(delay_list[0] - delay_list[1])
        max_jitter2 = abs(delay_list[1] - delay_list[2])
        max_ji = (max_jitter1 + max_jitter2) / 2
        # max_ji = [max_jitter1,max_jitter2]
        # max_ji = pd.concat(max_ji)
        return max_ji

