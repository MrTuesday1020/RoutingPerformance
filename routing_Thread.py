#!/usr/bin/python3
# COMP9331 Assignment2 RoutingPerformance
# z5092923 Wang Jintao
# z5104857 Shi Xiaoyun

import sched, time
from random import randint
from random import choice
import threading
import time
import sys

########################## Input Arguments ##########################
# network type values: CIRCUIT or PACKET
NETWORK_SCHEME = "CIRCUIT"
#NETWORK_SCHEME = sys.argv[1]
# routing scheme values: Shortest Hop Path (SHP), Shortest Delay Path (SDP) and Least Loaded Path (LLP)
ROUTING_SCHEME = "LLP"
#ROUTING_SCHEME = sys.argv[2]
# a file contains the network topology specification
TOPOLOGY_FILE = "topology.txt"
#TOPOLOGY_FILE = sys.argv[3]
# a file contains the virtual connection requests in the network
# workload_small.txt or workload.txt
WORKLOAD_FILE = "workload_small.txt"
#WORKLOAD_FILE = sys.argv[4]
# a positive integer value which show the number of packets per second which will be sent in each virtual connection.
PACKET_RATE = 3
#PACKET_RATE = int(sys.argv[5])

timeScale = 5

########################## Output  ##########################
# The total number of virtual connection requests.
NoOfReq = 0
# The total number of packets.
NoOfAllPkt = 0
# The number (and percentage) of successfully routed packets.
NoOfSuccPkt = 0
# The number (and percentage) of blocked packets.
NoOfBlkPkt = 0
# The total number of hops (i.e. links) consumed per successfully routed circuit. 
NoOfHops = 0
# The total source-to-destination cumulative propagation delay per successfully routed circuit.
PDelays = 0
# The total number of success requests
NoOfSuccReq = 0


########################## Graph ##########################
class Graph:
	# create a new graph
	# O(nV^2)	nV = 26
	def __init__(self,V = 26):
		self.edges = [[0 for x in range(V)] for y in range(V)]
		self.myedge = [[] for x in range(V)]
		self.vSet = [chr(x+65) for x in range(V)]
		self.nV = V
		self.nE = 0
	
	# vertices v and w , delay d, all capacities c, already used capacities s
	# O(1)
	def insertEdge(self,v,w,d,c,s = 0):
		v = ord(v) - 65
		w = ord(w) - 65
		d = int(d)
		c = int(c)
		if self.edges[v][w] == 0:
			self.edges[v][w] = [d,c,s];
			self.edges[w][v] = [d,c,s];
			self.myedge[v].append(w)
			self.myedge[w].append(v)
			self.nE += 1;
	
#	# return whether exist edge between two vertices
#	# O(1)
#	def adjacent(self,v,w):
#		if type(v) is str:
#			v = ord(v) - 65
#		if type(w) is str:
#			w = ord(w) - 65
#		return (self.edges[v][w] != 0)
	
	# occupy a capacity between v,w
	# O(1)
	def occupy(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] += 1
		self.edges[w][v][2] += 1

	# release a capacity between v,w
	# O(1)
	def release(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] -= 1
		self.edges[w][v][2] -= 1
	
	# return whether edge is blocked
	# O(1)
	def isBlock(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return (self.edges[v][w][1] == self.edges[v][w][2])
	
	# return delay
	# O(1)
	def delay(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][0]
	
	# return already used capacities s
	# O(1)
	def up(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][2]
	
	# return capacities c
	# O(1)	
	def down(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][1]
	
	# return all adjacent node
	# O(1)
	def edge(self,v):
		if type(v) is str:
			v = ord(v) - 65
		return self.myedge[v]

########################## Route Scheme ##########################
# Shortest Hop Path
# O(nV^2)
def SHP(graph,start,end):
	start = ord(start)-65
	dist = [float("inf") for x in range(graph.nV)]
	pred = [ -1 for x in range(graph.nV)]
	dist[start] = 0
	adjed = [start]
	visited = [start]
	while len(adjed) != 0:
		source = adjed.pop()
		edge = graph.edge(source)
		for i in edge:
			if i not in visited:
#		for i in range(graph.nV):
#			if graph.adjacent(source,i) and i not in visited:
				adjed.append(i)
				if dist[i] > dist[source] + 1:
					dist[i] = dist[source] + 1
					pred[i] = source
				elif dist[i] == dist[source] + 1:
					pred[i] = choice([source,pred[i]])
		visited.append(source)
	path = [end]
	end = ord(end)-65
	while dist[ord(path[-1])-65] != 0:
		path.append(chr(pred[end]+65))
		end = pred[end]
	path.reverse()
	return path

# Shortest Delay Path
# O(nV^2)
def SDP(graph,start,end):
	start = ord(start)-65
	dist = [float("inf") for x in range(graph.nV)]
	pred = [ -1 for x in range(graph.nV)]
	dist[start] = 0
	adjed = [start]
	visited = [start]
	while len(adjed) != 0:
		source = adjed.pop()
		edge = graph.edge(source)
		for i in edge:
			if i not in visited:
#		for i in range(graph.nV):
#			if graph.adjacent(source,i) and i not in visited:
				adjed.append(i)
				if dist[i] > dist[source] + graph.delay(source, i):
					dist[i] = dist[source] + graph.delay(source, i)
					pred[i] = source
				elif dist[i] == dist[source] + graph.delay(source,i):
					pred[i] = choice([source,pred[i]])
		visited.append(source)
	path = [end]
	end = ord(end)-65
	while dist[ord(path[-1])-65] != 0:
		end = pred[end]
		path.append(chr(end+65))
	path.reverse()
	return path

# Least Loaded Path
def LLP(graph,start,end):
	start = ord(start)-65
	dist = [float("inf") for x in range(graph.nV)]
	dist[start] = 0
	pred = [ -1 for x in range(graph.nV)]
	pred[start] = 0
	adjed = [start]
	visited = [start]
	while len(adjed) != 0:
		source = adjed.pop()
		edge = graph.edge(source)
		for i in edge:
			if i not in visited:
#		for i in range(graph.nV):
#			if graph.adjacent(source,i) and i not in visited:
				adjed.append(i)
				tmp = graph.up(source,i)*10000 / graph.down(source,i)
				if dist[i] > max(dist[source], tmp):
					dist[i] = max(dist[source], tmp)
					pred[i] = source
				elif dist[i] == max(dist[source], tmp):
					pred[i] = choice([source, pred[i]])
				
#				if dist_ratio[i] < (dist_up[source] + graph.up(source,i))/(dist_down[source] + graph.down(source,i)):
#					dist_up[i] = dist_up[source] + graph.up(source,i)
#					dist_down[i] = dist_down[source] + graph.down(source,i)
#					dist_ratio[i] = (dist_up[source] + graph.up(source,i))/(dist_down[source] + graph.down(source,i))
#					pred[i] = source
		visited.append(source)
	path = [end]
	end = ord(end)-65
	while pred[ord(path[-1])-65] != 0:
		end = pred[end]
		path.append(chr(end+65))
	path.reverse()
	return path
	
def dfs_LLP(graph,start,end):
	temp_path = [start]
	q = []
	q.append(temp_path)
	paths = []
	
	while len(q) != 0:
		tmp_path = q.pop()
		last_node = tmp_path[len(tmp_path)-1]
		if last_node == end:
			paths.append(tmp_path)
		for i in range(graph.nV):
			link_node = chr(i+65)
			if graph.adjacent(last_node,link_node):
				if link_node not in tmp_path:
					new_path = tmp_path + [link_node]
					q.append(new_path)
	great_ratio = float("-inf")
	for path in paths:
		path_up = 0
		path_down = 0
		for node in range(len(path)-1):
			path_up += graph.up(path[node],path[node+1])
			path_down += graph.down(path[node],path[node+1])
		path_ratio = path_up/path_down
		if path_ratio > great_ratio:
			great_ratio = path_ratio
			great_path = path
#	print(great_path)
	return great_path

########################## Thread ##########################
Lock = threading.Lock()
threads = []

class request (threading.Thread):
	def __init__(self, threadID, graph, startTime, source, destination, runTime):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.graph = graph
		self.startTime = startTime
		self.source = source
		self.destination = destination
		self.runTime = runTime
	
	def run(self):
		global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays, NoOfSuccReq, blocklist
		# CIRCUIT network: the connection is established from start to end
		if(NETWORK_SCHEME == "CIRCUIT"):
			interval = self.runTime
		# PACKET network: the request should establish connection every 1/PACKET_RATE seconds
		elif(NETWORK_SCHEME == "PACKET"):
			interval = 1 / PACKET_RATE / timeScale
		
		currentTime = 0.0
		while currentTime < self.runTime:
			currentTime += interval
			print("Request " + str(self.threadID) + " starts with path:", end='')
			if(ROUTING_SCHEME == "SHP"):
				path = SHP(self.graph, self.source, self.destination)
			elif(ROUTING_SCHEME == "SDP"):
				path = SDP(self.graph, self.source, self.destination)
			elif(ROUTING_SCHEME == "LLP"):
				path = LLP(self.graph, self.source, self.destination)
			else:
				pass
			print(path)
			Lock.acquire()
			isBlock = False
			for i in range(len(path)-1):
				isBlock = self.graph.isBlock(path[i],path[i+1])
				# if this sub path is blocked then break the loop and the whole path is blocked
				if isBlock:
					print(path)
					break
			# if the path is not blocked then get ont capacity of all the sub paths
			if not isBlock:
				for i in range(len(path)-1):
					self.graph.occupy(path[i],path[i+1])
				NoOfSuccPkt += int(interval * PACKET_RATE * timeScale)
				NoOfSuccReq += 1
				NoOfHops += len(path)
				delay = self.graph.delay(path[i],path[i+1])
				PDelays += delay
			else:
				NoOfBlkPkt += int(interval * PACKET_RATE * timeScale)
#				print("Request " + str(self.threadID) + " has been blocked ")
			Lock.release()
			if not isBlock:
				# the time the connection lasts
				time.sleep(interval)
				# release resources
				Lock.acquire()
				for i in range(len(path)-1):
					self.graph.release(path[i],path[i+1])
				Lock.release()
#				if(NETWORK_SCHEME == "CIRCUIT"):
#					print("Request " + str(self.threadID) + " durates {:.6f}".format(interval))
#				else:
#					print("Request " + str(self.threadID) + " starts a request after {:.6f}".format(currentTime - interval))

def doRequest(threadID, graph, startTime, source, destination, runTime):
	thread = request(threadID, graph, startTime, source, destination, runTime)
	thread.start()
	global threads
	threads.append(thread)


########################## Main ##########################
def main():
	global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays, threads
	# open and read TOPOLOGY_FILE
	with open(TOPOLOGY_FILE) as f:
		routers = [line.strip().split(" ") for line in f]

	# open and reand WORKLOAD_FILE
	with open(WORKLOAD_FILE) as f:
		requests = [line.strip().split(" ") for line in f]

	# compute statistics
	NoOfReq = len(requests)	
	for request in requests:
		NoOfAllPkt += int(float(request[3]) * PACKET_RATE)
	
	graph = Graph()
	for router in routers:
		graph.insertEdge(router[0], router[1], router[2], router[3])
#	graph._vSet()
	
#	x = SHP(graph, 'K', 'D')
#	y = SDP(graph, 'F', 'L')
#	z = dfs_LLP(graph, 'K', 'D')
#	print(x)
#	print(y)
#	print(z)
	
	# init a schedule
	schedule = sched.scheduler (time.time, time.sleep)
	# put requests into schedule
	for i in range(len(requests)):
		startTime = float(requests[i][0]) / timeScale
		source = requests[i][1]
		destination = requests[i][2]
		runTime = float(requests[i][3]) / timeScale
		schedule.enter(startTime, 0, doRequest, (i, graph, startTime, source, destination, runTime))
	
	start  = time.time()
	
	schedule.run()
	
	for t in threads:
		t.join()
	
	print("RuntTime:{:.2f}".format(time.time()-start))
	
	print("total number of virtual connection requests:", NoOfReq)
	print("total number of packets:", NoOfAllPkt)
	print("number of successfully routed packets:", NoOfSuccPkt)
	print("percentage of successfully routed packets: {:.2f}".format(NoOfSuccPkt / NoOfAllPkt * 100))
	print("number of blocked packets:", NoOfBlkPkt)
	print("percentage of blocked packets: {:.2f}".format(NoOfBlkPkt / NoOfAllPkt * 100))
	print("average number of hops per circuit: {:.2f}".format(NoOfHops / NoOfSuccReq))
	print("average cumulative propagation delay per circuit: {:.2f}".format(PDelays / NoOfSuccReq))

if __name__ == "__main__":
	main()