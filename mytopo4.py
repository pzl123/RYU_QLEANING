# -*- coding:utf-8 -*-
"""
作者:${彭忠林}
日期:2023年04月13日
"""
#创建网络拓扑，代码可以直接使用
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController,CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.net import Mininet
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
import time,os

from mininet.node import OVSSwitch

class MyTopo( Topo ):
    def __init__( self ):
        "Create custom topo."
        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        s1 = self.addSwitch('s1', cls=OVSSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSSwitch, protocols='OpenFlow13')
        s5 = self.addSwitch('s5', cls=OVSSwitch, protocols='OpenFlow13')
        s6 = self.addSwitch('s6', cls=OVSSwitch, protocols='OpenFlow13')
        s7 = self.addSwitch('s7', cls=OVSSwitch, protocols='OpenFlow13')
        s8 = self.addSwitch('s8', cls=OVSSwitch, protocols='OpenFlow13')
        s9 = self.addSwitch('s9', cls=OVSSwitch, protocols='OpenFlow13')

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s9)
        self.addLink(h3, s9)
        self.addLink(h4, s9)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s1, s4)
        self.addLink(s2, s5)
        self.addLink(s3, s6)
        self.addLink(s4, s5)
        self.addLink(s5, s6)
        self.addLink(s4, s7)
        self.addLink(s5, s8)
        self.addLink(s6, s9)
        self.addLink(s7, s8)
        self.addLink(s8, s9)

topos = { 'mytopo': ( lambda: MyTopo() ) }


