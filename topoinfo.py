from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event, app_manager
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER,DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import api as topo_api
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib import hub

from ryu.topology import event, switches
from ryu.topology.api import get_all_switch, get_link, get_switch
from ryu.lib.ofp_pktinfilter import packet_in_filter, RequiredTypeFilter

import networkx as nx

class topoinfo(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(topoinfo, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.link_to_port = {}       # (src_dpid,dst_dpid)->(src_port,dst_port) 记录交换机之间的端口关系
        self.access_table = {}       # {(sw,port) :[host1_ip]} 记录交换机与主机的连接关系
        self.switch_port_table = {}  # dpip->port_num
        self.access_ports = {}       # dpid->port_num
        self.interior_ports = {}     # dpid->port_num  交换机与交换机之间的连接链路
        self.graph = nx.DiGraph()
        self.link_max_bw = 1#最大带宽
        self.dps = {} #dp表
        self.tx_bytes = {}
        self.port_speed ={}#交换机与控制器之间的链路速率
        self.port_bandwidth = {}  # 交换机与控制器链路的链路使用率
        self.switches = None
        self.discover_thread = hub.spawn(self._discover)

    def _discover(self):
        i = 0
        while True:
            for datapath in self.dps.values():
                self.request_stats(datapath)
            self.get_topology(None)
            hub.sleep(1)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])  # 监听事件
    def _state_change_handler(self, ev):  # 将在线的交换机信息放在dp表内
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:  # 交换机上线
            if datapath.id not in self.dps:  # 如果该dpid不在dp表内，那么学习
                #self.logger.debug('-----注册交换机------: %016x', datapath.id)  # 注册
                self.dps[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:  # 交换机下线
            if datapath.id in self.dps:  # 交换机在dp表内
                #self.logger.debug('-----注销交换机------: %016x', datapath.id)  # 注销
                del self.dps[datapath.id]

    def request_stats(self, datapath):
        """
            Sending request msg to datapath
        """
        #self.logger.debug('-------向该交换机发送状态请求-------: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # 上方为解析流表的基本步骤
        #req = parser.OFPFlowStatsRequest(datapath)  # 请求流表项
        #datapath.send_msg(req)  # 下发
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)  # 请求端口数据
        datapath.send_msg(req)

    ''''@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        self.logger.info('------触发端口统计-----')
        body = ev.msg.body

        self.logger.info('datapath              端口号'
                         '接收数据包  接受字节  接收错误 '
                         '发送数据包  发送字节  发送错误')
        self.logger.info('----------------  -------- '
                         '------------     ----------     -------- '
                         '------------     ----------     --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %9x %9d %9d %9d %9d %9d %9d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        self.logger.info('-----触发流表统计------')
        self.logger.info('datapath         '
                         '入端口    目的地址           '
                         '出端口    包    字节')
        self.logger.info('---------------- '
                         '-------- ---------        '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)'''

    def get_topology(self, ev):
        """
            Get topology info
        """
        # print "get topo"
        switch_list = get_all_switch(self)
        # print switch_list
        self.create_port_map(switch_list)
        self.switches = self.switch_port_table.keys()
        links = get_link(self.topology_api_app, None)
        self.create_interior_links(links)
        self.create_access_ports()
        self.get_graph()

    def create_port_map(self, switch_list):
        for sw in switch_list:
            dpid = sw.dp.id
            self.graph.add_node(dpid)
            self.dps[dpid] = sw.dp
            #初始化字典
            self.switch_port_table.setdefault(dpid, set())#获取所有交换机在用的端口
            self.interior_ports.setdefault(dpid, set())#以dpid为key，values为ports的列表
            self.access_ports.setdefault(dpid, set())#相邻的端口

            for p in sw.ports:
                self.switch_port_table[dpid].add(p.port_no)

    def create_interior_links(self, link_list):
        for link in link_list:
            src = link.src
            dst = link.dst
            self.link_to_port[(src.dpid, dst.dpid)] = (src.port_no, dst.port_no)

            # Find the access ports and interiorior ports
            if link.src.dpid in self.switches:
                self.interior_ports[link.src.dpid].add(link.src.port_no)
            if link.dst.dpid in self.switches:
                self.interior_ports[link.dst.dpid].add(link.dst.port_no)
            #存入交换机之间连接的端口

    def create_access_ports(self):
        for sw in self.switch_port_table:
            all_port_table = self.switch_port_table[sw]#sw为字典key 不是value
            interior_port = self.interior_ports[sw]
            self.access_ports[sw] = all_port_table - interior_port
            #将全部端口减去交换机之间连接的端口
            #就是交换机连接主机的端口

    def get_graph(self):
        link_list = topo_api.get_all_link(self)
        for link in link_list:
            src_dpid = link.src.dpid
            dst_dpid = link.dst.dpid
            src_port = link.src.port_no
            dst_port = link.dst.port_no
            port_key = (src_dpid, src_port)
            weight = 0
            if port_key in self.controller_to_switches_link_speed.keys():
                weight = self.controller_to_switches_link_speed[port_key]
            self.graph.add_edge(src_dpid, dst_dpid,
                                src_port=src_port,
                                dst_port=dst_port,
                                weight=weight+0.001)
        return self.graph

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath

        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
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
                self.register_access_info(datapath.id, in_port, src_ipv4, src_mac)

        if arp_pkt:
            arp_src_ip = arp_pkt.src_ip
            arp_dst_ip = arp_pkt.dst_ip
            mac = arp_pkt.src_mac

            # Record the access info
            self.register_access_info(datapath.id, in_port, arp_src_ip, mac)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def link_state_statistics(self, ev):
        """
            Save port's stats info
            Calculate port's speed and save it.
        """
        body = ev.msg.body
        dpid = ev.msg.datapath.id

        for stat in sorted(body, key=attrgetter('port_no')):
            port_no = stat.port_no
            if port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (dpid, port_no)
                value = stat.tx_bytes
                if key in self.tx_bytes.keys():
                    speed = (value - self.tx_bytes[key]) / 1024 / 1024 # MB/s
                    self.port_speed[key] = speed
                    self.port_bandwidth[key] = (speed / self.link_max_bw)*100
                    '''print('---------触发链路函数计算--------')
                    print('-----------'
                                     '%d 号OVS  %d 端口的链路速度: %f ' + 'Mb/s', key[0], key[1], speed)
                    print('-----------'
                                     '其链路利用率为: %f ', (speed / self.link_max_bw) * 100)'''
                self.tx_bytes[key] = value

    def register_access_info(self, dpid, in_port, ip, mac):
        """
            Register access host info into access table.
        """
        # print "register " + ip
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

    def get_host_location(self, host_ip):
        """
            Get host location info:(datapath, port) according to host ip.
        """
        for key in self.access_table.keys():
            if self.access_table[key][0] == host_ip:
                return key
        self.logger.debug("%s location is not found." % host_ip)
        return None

    def get_switches(self):
        return self.switches

    def get_links(self):
        return self.link_to_port

    def get_datapath(self, dpid):
        if dpid not in self.dps:#交换机不在列表的话
            switch = topo_api.get_switch(self, dpid)[0]
            self.dps[dpid] = switch.dp#加入列表
            return switch.dp#返回该交换机的id
        return self.dps[dpid]#在的话直接返回交换机id

    def set_shortest_path(self,
                          ip_src,
                          ip_dst,
                          src_dpid,
                          dst_dpid,
                          to_port_no,
                          to_dst_match,
                          pre_actions=[]
                          ):
        if nx.has_path(self.graph, src_dpid, dst_dpid):#存在路径?
            path = nx.shortest_path(self.graph, src_dpid, dst_dpid, weight="weight")#path返回的是列表 path=[1,2,3,4]
        else:
            path = None
        if path is None:
            self.logger.info("Get path failed.")
            return 0

        if self.get_host_location(ip_src)[0] == src_dpid:
            print("path from " + ip_src + " to " + ip_dst +':', end="")
            print(ip_src + ' ->', end="")
            for sw in path:
                print(str(sw) + ' ->', end="")
            print(ip_dst)

        if len(path) == 1:#直连
            dp = self.get_datapath(src_dpid)
            actions = [dp.ofproto_parser.OFPActionOutput(to_port_no)]
            self.add_flow(dp, 10, to_dst_match, pre_actions+actions, idle_timeout=100, hard_timeout=100)
            port_no = to_port_no
        else:
            self.install_path(to_dst_match, path, pre_actions)#安装路径流表
            dst_dp = self.get_datapath(dst_dpid)#得到目的交换机的id
            actions = [dst_dp.ofproto_parser.OFPActionOutput(to_port_no)]
            self.add_flow(dst_dp, 10, to_dst_match, pre_actions+actions, idle_timeout=100, hard_timeout=100)
            port_no = self.graph[path[0]][path[1]]['src_port']

        return port_no

    '''def select_path(self, paths):
        min_bw_used = 0xffffff
        selected_path_index = 0
        for i in range(len(paths)):
            max_bw_used = 0
            path = paths[i]
            for j in range(len(path) - 1):
                if self.graph[path[j]][path[j+1]]["weight"] > max_bw_used:
                    max_bw_used = self.graph[path[j]][path[j+1]]["weight"]
            if max_bw_used < min_bw_used:
                min_bw_used = max_bw_used
                selected_path_index = i
        return paths[selected_path_index]'''

    def install_path(self, match, path, pre_actions=[]):#path=[a,b,c,d,e,f,g] 字母为dpid
        for index, dpid in enumerate(path[:-1]):
            port_no = self.graph[path[index]][path[index + 1]]['src_port']#获取转发端口
            dp = self.get_datapath(dpid)
            actions = [dp.ofproto_parser.OFPActionOutput(port_no)]
            self.add_flow(dp, 10, match, pre_actions+actions, idle_timeout=100, hard_timeout=100) #添加到流表内

    def add_flow(self, dp, p, match, actions, idle_timeout=0, hard_timeout=0):
        #self.logger.info('--------触发Add_Flow中-------')
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=p,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

