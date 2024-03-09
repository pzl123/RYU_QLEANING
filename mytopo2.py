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

        # s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13',dpid='000000000000001')
        # s2 = self.addSwitch('s2', cls=OVSKernelSwitch,  protocols='OpenFlow13',dpid='000000000000002')
        # s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000003')
        # s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000004')
        # s5 = self.addSwitch('s5', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000005')
        # s6 = self.addSwitch('s6', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000006')
        # s7 = self.addSwitch('s7', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000007')
        # s8 = self.addSwitch('s8', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000008')
        # s9 = self.addSwitch('s9', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000009')
        # s10 = self.addSwitch('s10', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000010')
        # s11 = self.addSwitch('s11', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000011')
        # s12 = self.addSwitch('s12', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000012')
        # s13 = self.addSwitch('s13', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000013')
        # s14 = self.addSwitch('s14', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000014')
        # s15 = self.addSwitch('s15', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000015')
        # s16 = self.addSwitch('s16', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000016')
        # s17 = self.addSwitch('s17', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000017')
        # s18 = self.addSwitch('s18', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000018')
        # s19 = self.addSwitch('s19', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000019')
        # s20 = self.addSwitch('s20', cls=OVSKernelSwitch, protocols='OpenFlow13', dpid='000000000000020')

        # s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s5 = self.addSwitch('s5', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s6 = self.addSwitch('s6', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s7 = self.addSwitch('s7', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s8 = self.addSwitch('s8', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s9 = self.addSwitch('s9', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s10 = self.addSwitch('s10', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s11 = self.addSwitch('s11', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s12 = self.addSwitch('s12', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s13 = self.addSwitch('s13', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s14 = self.addSwitch('s14', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s15 = self.addSwitch('s15', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s16 = self.addSwitch('s16', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s17 = self.addSwitch('s17', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s18 = self.addSwitch('s18', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s19 = self.addSwitch('s19', cls=OVSKernelSwitch, protocols='OpenFlow13')
        # s20 = self.addSwitch('s20', cls=OVSKernelSwitch, protocols='OpenFlow13')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch,)
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch,)
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, )
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch,)
        s5 = self.addSwitch('s5', cls=OVSKernelSwitch, )
        s6 = self.addSwitch('s6', cls=OVSKernelSwitch, )
        s7 = self.addSwitch('s7', cls=OVSKernelSwitch,)
        s8 = self.addSwitch('s8', cls=OVSKernelSwitch, )
        s9 = self.addSwitch('s9', cls=OVSKernelSwitch,)
        s10 = self.addSwitch('s10', cls=OVSKernelSwitch,)
        s11 = self.addSwitch('s11', cls=OVSKernelSwitch,)
        s12 = self.addSwitch('s12', cls=OVSKernelSwitch, )
        s13 = self.addSwitch('s13', cls=OVSKernelSwitch,)
        s14 = self.addSwitch('s14', cls=OVSKernelSwitch,)
        s15 = self.addSwitch('s15', cls=OVSKernelSwitch,)
        s16 = self.addSwitch('s16', cls=OVSKernelSwitch,)
        s17 = self.addSwitch('s17', cls=OVSKernelSwitch,)
        s18 = self.addSwitch('s18', cls=OVSKernelSwitch,)
        s19 = self.addSwitch('s19', cls=OVSKernelSwitch,)
        s20 = self.addSwitch('s20', cls=OVSKernelSwitch,)

        # info( '*** Add hosts\n')
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)
        h5 = self.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None)
        h6 = self.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None)
        h7 = self.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None)
        h8 = self.addHost('h8', cls=Host, ip='10.0.0.8', defaultRoute=None)

        # info( '*** Add links\n')
        self.addLink(s1, s5, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s1, s9, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s1, s13, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s1, s17, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s2, s5, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s2, s9, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s2, s13, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s2, s17, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s3, s6, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s3, s10, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s3, s14, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s3, s18, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s4, s10, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s4, s14, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s4, s6, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s4, s18, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s5, s7, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s5, s8, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s6, s7, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s6, s8, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s9, s11, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s9, s12, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s10, s11, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s10, s12, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s13, s15, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s13, s16, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s14, s15, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s14, s16, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s17, s19, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s17, s20, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s18, s19, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(s18, s20, bw=100, delay='0.5ms', loss=0.1)

        self.addLink(h1, s7, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h2, s8, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h3, s11, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h4, s12, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h5, s15, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h6, s16, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h7, s19, bw=100, delay='0.5ms', loss=0.1)
        self.addLink(h8, s20, bw=100, delay='0.5ms', loss=0.1)

topos = { 'mytopo': ( lambda: MyTopo() ) }

"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""



# class MyTopo(Topo):
#     "Simple topology example."
#
#     def build(self):
#         "Create custom topo."
#
#         # Add hosts and switches
#         h1 = self.addHost('h1')
#         h2 = self.addHost('h2')
#         h3 = self.addHost('h3')
#         h4 = self.addHost('h4')
#
#         s1 = self.addSwitch('s1', cls=OVSSwitch, protocols='OpenFlow13')
#         s2 = self.addSwitch('s2', cls=OVSSwitch, protocols='OpenFlow13')
#         s3 = self.addSwitch('s3', cls=OVSSwitch, protocols='OpenFlow13')
#         s4 = self.addSwitch('s4', cls=OVSSwitch, protocols='OpenFlow13')
#         s5 = self.addSwitch('s5', cls=OVSSwitch, protocols='OpenFlow13')
#         s6 = self.addSwitch('s6', cls=OVSSwitch, protocols='OpenFlow13')
#         s7 = self.addSwitch('s7', cls=OVSSwitch, protocols='OpenFlow13')
#         s8 = self.addSwitch('s8', cls=OVSSwitch, protocols='OpenFlow13')
#         s9 = self.addSwitch('s9', cls=OVSSwitch, protocols='OpenFlow13')
#
#         # Add links
#         self.addLink(h1, s1)
#         self.addLink(h2, s9)
#         self.addLink(h3, s9)
#         self.addLink(h4, s9)
#         self.addLink(s1, s2)
#         self.addLink(s2, s3)
#         self.addLink(s1, s4)
#         self.addLink(s2, s5)
#         self.addLink(s3, s6)
#         self.addLink(s4, s5)
#         self.addLink(s5, s6)
#         self.addLink(s4, s7)
#         self.addLink(s5, s8)
#         self.addLink(s6, s9)
#         self.addLink(s7, s8)
#         self.addLink(s8, s9)
#
#
# topos = {'mytopo': (lambda: MyTopo())}

