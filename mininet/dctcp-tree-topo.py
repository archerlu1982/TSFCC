from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from multiprocessing import Process
from time import sleep
import threading
import os;
import subprocess
from queuelength import monitor_qlen

class MyTopology(Topo):
    def build(self):
        os.system("sysctl net.ipv4.tcp_congestion_control=dctcp")
        os.system("sysctl net.ipv4.tcp_ecn=1")
        os.system("sysctl net.ipv4.tcp_ecn_fallback=0")
        # 创建核心交换机
        core_switch = self.addSwitch('s1')

        # 创建汇聚层交换机
        aggregation_switch1 = self.addSwitch('s2')
        aggregation_switch2 = self.addSwitch('s3')

        # 创建边缘交换机
        edge_switch1 = self.addSwitch('s4')
        edge_switch2 = self.addSwitch('s5')
        edge_switch3 = self.addSwitch('s6')
        edge_switch4 = self.addSwitch('s7')

        # 创建主机
        for i in range(1, 5):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch1, host)

        for i in range(5, 6):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch2, host)

        for i in range(6, 7):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch3, host)

        for i in range(7, 38):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch4, host)

        # 创建链路
        self.addLink(core_switch, aggregation_switch1)
        self.addLink(core_switch, aggregation_switch2)
        self.addLink(aggregation_switch1, edge_switch1)
        self.addLink(aggregation_switch1, edge_switch2)
        self.addLink(aggregation_switch2, edge_switch3)
        self.addLink(aggregation_switch2, edge_switch4)
def set_qdisc(eth):
    os.system("tc qdisc add dev %s root handle 1: htb default 1" % eth)
    os.system("tc class add dev %s parent 1: classid 1:1 htb rate 1000mbit" % eth)
    os.system("tc qdisc add dev %s parent 1:1 handle 2: red limit 150000b min 30000b max 30001b avpkt 1500 burst 100 "
              "ecn "
              "probability 1 bandwidth 1000Mbit" % eth)
    os.system("tc qdisc add dev %s parent 2:1 handle 3: netem delay 100us" % eth)
    # os.system("tc filter add dev %s protocol ip parent 1: prio 0 u32 match ip src 0.0.0.0/0 flowid 1:1" % eth)

def start_iperf(net):
    h37 =net.get('h37')
    print("Starting iperf server...")
    h37.popen("iperf -s -p 5001 &")
    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    output = subprocess.check_output(["sysctl", "net.ipv4.tcp_congestion_control"])
    control = output.decode().strip().split("=")[1]
    if control == " dctcp":
        print("using dctcp")
        for i in range(1, 8, 1):  # L1+L2+L3 , set tc in every switch
            s = net.get('s%s' % i)
            for intf in s.intfList():
                inter_face = str(intf)
                if inter_face != "lo":
                    set_qdisc(inter_face)
    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h1.popen("iperf -c %s -t 10 " % (h37.IP()))
    h2.popen("iperf -c %s -t 10 " % (h37.IP()))
    h3.popen("iperf -c %s -t 10 " % (h37.IP()))
    for i in range(7, 37):
        mouse_pacp_file_path = './iperf-test/test-topo2/h'+str(i)+'.pcap'
        h = 'h' + str(i)
        host = net.get(h)
        host.popen("tcpdump -w %s" % (mouse_pacp_file_path))
    print("Finishing iperf server...")


def iperf_command(host, h37):
        host.popen("iperf -c %s -n 512K" % (h37.IP()))

def random_generate_flows(net):
    h37 = net.get('h37')
    start_event = threading.Event()

    def thread_func(host):
        start_event.wait()
        iperf_command(host, h37)

    threads = []
    for i in range(7, 37):
        h = 'h' + str(i)
        host = net.get(h)
        thread = threading.Thread(target=thread_func, args=(host,))
        threads.append(thread)

    start_event.set()

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

def create_topology():
    topo = MyTopology()
    net = Mininet(topo=topo,host=CPULimitedHost, link=TCLink, controller=RemoteController)
    # 启动拓扑
    net.start()
    net.pingAll()
    sleep(1)
    start_iperf(net)
    sleep(3)
    random_generate_flows(net)
    sleep(8)
    # CLI( net )
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    create_topology()