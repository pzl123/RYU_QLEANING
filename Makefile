.PYONY: clean

topo:
	mn --custom mytopo2.py --topo mytopo --controller remote --mac

topo2:
	mn --custom mytopo3.py --topo mytopo --controller remote --mac
	# h1
	#  \
	#   1 - 2 - 3
	#   |   |   |
	#   4 - 5 - 6
	#   |   |   |
	#   7 - 8 - 9
	#         / | \
    #        h2 h3 h4
topo3:
	mn --custom mytopo3.py --topo mytopo --switch=ovsk,failMode='standalone',stp=True


test:
	ryu-manager ecmp.py topoinfo.py --observe-links

test2:
	ryu-manager ryu_easy.py delay.py --observe-links




clean:
	mn -c


