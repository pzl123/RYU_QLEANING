# -*- coding:utf-8 -*-
"""
作者:${彭忠林}
日期:2023年10月16日

# File       : net_delay.py
# Data       ：4/3/23 1:26 AM
# Author     ：pzl
# version    ：python 3.8
# Description：
"""
# from __future__ import division
from ryu import cfg
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.topology.switches import Switches
from ryu.topology.switches import LLDPPacket
import networkx as nx
import time

DISCOVERY_PERIOD = 10  # For discovering topology.
MONITOR_PERIOD = 10  # For monitoring traffic
DELAY_DETECTING_PERIOD = 2  # For detecting link delay.
TOSHOW = True  # For showing information in terminal
MAX_CAPACITY = 281474976710655  # Max capacity of link
sending_echo_request_interval = 0.5


class NetworkDelayDetector(app_manager.RyuApp):
    """
        NetworkDelayDetector is a Ryu app for collecting link delay.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkDelayDetector, self).__init__(*args, **kwargs)
        self.name = 'net_delay'

        self.echo_delay_table = {}  # {dpid: ryu_ofps_delay}  echo_delay
        self.lldp_delay_table = {}  # {src_dpid: {dst_dpid: delay}} lldp_delay
        self.ture_delay = {} # {src_dpid: {dst_dpid: delay}}  ture_delay

        # Get the active object of swicthes and awareness module.
        # So that this module can use their data.
        self.switch_module = lookup_service_brick('switches')
        self.network_structure = lookup_service_brick('structure_awarness')
        # self.network_monitor = lookup_service_brick('net_monitor')

        self._delay_thread = hub.spawn(self.scheduler)

    def scheduler(self):
        while True:
            self._send_echo_request()
            self.create_delay_graph()
            # self.show_delay_stats()
            # print(self.ture_delay)
            # print("access_tables is {}".format(self.network_structure.access_table))
            hub.sleep(DELAY_DETECTING_PERIOD)

    # 利用echo发送时间，与接收时间相减
    # 1. 发送echo request
    def _send_echo_request(self):
        """ 发送echo请求"""
        # datapaths_table = self.network_monitor.datapaths_table.values() # {dpid:datapath} 得到所有的datapath
        datapaths_table = self.network_structure.datapaths.values()  # {dpid:datapath} 得到所有的datapath
        if datapaths_table is not None:
            for datapath in list(datapaths_table):
                parser = datapath.ofproto_parser
                data = time.time()
                echo_req = parser.OFPEchoRequest(datapath, b"%.12f" % data)
                datapath.send_msg(echo_req)
                hub.sleep(sending_echo_request_interval)  # 防止发太快，这边收不到

    # 2. 接收echo reply
    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def _ehco_reply_handler(self, ev):
        now_timestamp = time.time()
        data = ev.msg.data
        ryu_ofps_delay = now_timestamp - eval(data)  # 现在时间减去发送的时间
        self.echo_delay_table[ev.msg.datapath.id] = ryu_ofps_delay

    # 利用LLDP时延
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """ 解析LLDP包, 这个处理程序可以接收所有可以接收的数据包, swicthes.py l:769"""
        # print("detector---> PacketIn")
        try:
            recv_timestamp = time.time()
            msg = ev.msg
            dpid = msg.datapath.id
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            if self.switch_module is None:
                self.switch_module = lookup_service_brick('switches')
            # print("---> self.switch_module.ports", self.switch_module.ports)

            for port in self.switch_module.ports.keys():
                if src_dpid == port.dpid and src_port_no == port.port_no:
                    send_timestamp = self.switch_module.ports[port].timestamp
                    if send_timestamp:
                        delay = recv_timestamp - send_timestamp
                        # else:
                        #     delay = 0
                        self.lldp_delay_table.setdefault(src_dpid, {})
                        self.lldp_delay_table[src_dpid][dpid] = delay  # 存起来
        except LLDPPacket.LLDPUnknownFormat as e:
            return

    def create_delay_graph(self):
        # 遍历所有的边
        # print('---> create delay graph')
        for src, dst in self.network_structure.graph.edges:
            delay = self.calculate_delay(src, dst)
            self.network_structure.graph[src][dst]['delay'] = delay * 1000  # ms
            # self.network_structure.graph[src].get(dst).get('delay') = delay * 1000  # ms
        # print("--->" * 2, self.network_structure.count + 1)

    def calculate_delay(self, src, dst):
        """
                        ┌------Ryu------┐
                        |               |
        src echo latency|               |dst echo latency
                        |               |
                    SwitchA------------SwitchB
                         --->fwd_delay--->
                         <---reply_delay<---
        """

        # fwd_delay = self.lldp_delay_table[src][dst]
        # reply_delay = self.lldp_delay_table[dst][src]
        # ryu_ofps_src_delay = self.echo_delay_table[src]
        # ryu_ofps_dst_delay = self.echo_delay_table[dst]

        fwd_delay = self.lldp_delay_table[src].get(dst,0)
        reply_delay = self.lldp_delay_table[dst].get(src,0)
        ryu_ofps_src_delay = self.echo_delay_table.get(src,0)
        ryu_ofps_dst_delay = self.echo_delay_table.get(dst,0)

        delay = (fwd_delay + reply_delay - ryu_ofps_src_delay - ryu_ofps_dst_delay) / 2
        return max(delay, 0)

    def show_delay_stats(self):
        self.logger.info("==============================DDDD delay=================================")
        self.logger.info("src    dst :    delay")
        for src in self.lldp_delay_table.keys():
            for dst in self.lldp_delay_table[src].keys():
                delay = self.lldp_delay_table[src][dst]
                self.logger.info("%s <---> %s : %s", src, dst, delay)
                # self.ture_delay[src][dst] = delay


    @staticmethod
    def _save_stats(_dict, key, value, keep):
        if key not in _dict:
            _dict[key] = []
        _dict[key].append(value)

        if len(_dict[key]) > keep:
            _dict[key].pop(0)  # 弹出最早的数据




