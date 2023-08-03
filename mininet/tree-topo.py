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

class MyTopology(Topo):
    def build(self):
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
            self.addLink(edge_switch1, host ,bw=1000, delay='100us', max_queue_size=100)

        for i in range(5, 6):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch2, host ,bw=1000, delay='100us', max_queue_size=100)

        for i in range(6, 7):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch3, host ,bw=1000, delay='100us', max_queue_size=100)

        for i in range(7, 38):
            host = self.addHost('h{}'.format(i))
            self.addLink(edge_switch4, host ,bw=1000, delay='100us', max_queue_size=100)

        # 创建链路
        self.addLink(core_switch, aggregation_switch1 ,bw=1000, delay='100us', max_queue_size=100)
        self.addLink(core_switch, aggregation_switch2 ,bw=1000, delay='100us', max_queue_size=100)
        self.addLink(aggregation_switch1, edge_switch1 ,bw=1000, delay='100us', max_queue_size=100)
        self.addLink(aggregation_switch1, edge_switch2 ,bw=1000, delay='100us', max_queue_size=100)
        self.addLink(aggregation_switch2, edge_switch3 ,bw=1000, delay='100us', max_queue_size=100)
        self.addLink(aggregation_switch2, edge_switch4 ,bw=1000, delay='100us', max_queue_size=100)

def start_iperf(net):
    h37 =net.get('h37')
    print("Starting iperf server...")
    h37.popen("iperf -s -p 5001 &")
    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
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
        host.popen("iperf -c %s -i 0.1 -n 512K" % (h37.IP()))

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
    # sleep(3)
    net.pingAll()
    sleep(3)
    start_iperf(net)
    sleep(3)
    random_generate_flows(net)
    sleep(8)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    create_topology()