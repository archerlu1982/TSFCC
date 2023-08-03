from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
from mininet.node import CPULimitedHost
from mininet.node import RemoteController
from time import sleep
import threading

class MyTopology(Topo):
    def build(self):
        # 创建交换机
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # 创建主机
        h44 = self.addHost('h44')
        h45 = self.addHost('h45')
        # 创建链路
        for i in range(1, 9):
            host = self.addHost('h{}'.format(i))
            self.addLink(s1, host ,bw=1000, delay='50us', max_queue_size=100)
        self.addLink(s2, h44 ,bw=1000, delay='50us', max_queue_size=100)
        self.addLink(s2, h45 ,bw=1000, delay='50us', max_queue_size=100)
        self.addLink(s1, s2 ,bw=1000, delay='50us', max_queue_size=100)
topos = { 'test1': ( lambda: MyTopology() ) }

# def set_qdisc(eth):
#     os.system("tc qdisc add dev %s root handle 1: htb default 1" % eth)
#     os.system("tc class add dev %s parent 1: classid 1:1 htb rate 1000mbit ceil 1000mbit" % eth)
#     os.system("tc qdisc add dev %s parent 1:1 handle 10: netem limit 100 delay 2ms" % eth)
#     os.system("tc class add dev %s parent 1: classid 1:10 htb rate 1000mbit ceil 1000mbit" % eth)
#     os.system("tc qdisc add dev %s parent 1:10 handle 5: netem limit 100 delay 2ms" % eth)
#     os.system("tc filter add dev %s parent 1: prio 1 protocol ip u32 match ip protocol 6 0xff match u8 0x02 0xff at 33 flowid 1:10" % eth)
#     os.system("tc filter add dev %s parent 1: prio 1 protocol ip u32 match ip protocol 6 0xff match u8 0x12 0xff at 33 flowid 1:10" % eth)
#     os.system("tc filter add dev %s parent 1: prio 1 protocol ip u32 match ip protocol 6 0xff match u8 0x11 0xff at 33 flowid 1:10" % eth)
#     os.system("tc filter add dev %s parent 1: prio 1 protocol ip u32 match ip protocol 6 0xff match u8 0x19 0xff at 33 flowid 1:10" % eth)
# tc qdisc add dev s1-eth1 root handle 1: htb default 1
# tc class add dev s1-eth1 parent 1: classid 1:1 htb rate 1000mbit ceil 1000mbit
# tc qdisc add dev s1-eth1 parent 1:1 handle 10: netem limit 100 delay 100us
# tc class add dev s1-eth1 parent 1: classid 1:10 htb rate 1000mbit ceil 1000mbit
# tc qdisc add dev s1-eth1 parent 1:10 classid 5: netem limit 100 delay 100us
# tc filter add dev s1-eth1 parent 1: prio 1 protocol ip u32 match ip protocol 6 0xff match u8 0x02 0xff at 33 flowid 1:1

def start_iperf(net):
    h44 =net.get('h44')
    h45 =net.get('h45')
    # s1 = net.get('s1')
    # for i in range(1, 3, 1):  # L1+L2+L3 , set tc in every switch
    #         s = net.get('s%s' % i)
    #         for intf in s.intfList():
    #             inter_face = str(intf)
    #             if inter_face != "lo":
    #                 set_qdisc(inter_face)
    print("Starting iperf server...")
    # pcap_file_path = './iperf-test/test-topo1/h34.pcap'
    # h34.popen("tcpdump -w %s" % (pcap_file_path))
    h44.popen("iperf -s -p 5001 &")
    h45.popen("iperf -s -p 5001 &")
    # mouse_pcap_file_path = './iperf-test/test-topo1/h44.pcap'
    # h44.popen("tcpdump -w %s" % (mouse_pcap_file_path))
    # for i in range(4, 34):
    #     mouse_pcap_file_path = './iperf-test/test-topo1/h'+str(i)+'.pcap'
    #     h = 'h' + str(i)
    #     host = net.get(h)
    #     host.popen("tcpdump -w %s" % (mouse_pcap_file_path))
    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    for i in range(1,3):
        h ='h'+str(i)
        host = net.get(h)
        # host.popen("iperf -c %s -t 60 &" % (h16.IP()))
        host.popen("iperf -c %s -t 10 " % (h45.IP()))
    print("Finishing iperf server...")

# def random_generate_flows(net):
#     h34 =net.get('h34')
#     for i in range(4,34):
#         h ='h'+str(i)
#         host = net.get(h)
#         # packet_size = random.randint(16,128)
#         file_path = './iperf-test/test-topo1/h'+str(i)+'.txt'
#         with open(file_path, 'w') as file:
#             host.popen("iperf -c %s -i 0.1 -n 512K &" % (h34.IP()), stdout=file)
def iperf_command(host, h44):
    host.popen("iperf -c %s -n 512K -P 7" % (h44.IP()))

def random_generate_flows(net):
    h44 = net.get('h44')
    start_event = threading.Event()

    def thread_func(host):
        start_event.wait()
        iperf_command(host, h44)

    threads = []
    for i in range(4, 9):
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
    s2 = net.get('s2')
    # goodput_file_path = './iperf-test/test-topo1/s1.pcap'
    # s1.popen("tcpdump -i s1-eth34 -w %s" % (goodput_file_path))
    elephant_goodput_file_path = './iperf-test/test-topo1/s2_elephant.pcap'
    s2.popen("tcpdump -i s2-eth2 -w %s" % (elephant_goodput_file_path))
    mouse_goodput_file_path = './iperf-test/test-topo1/s2_mouse.pcap'
    s2.popen("tcpdump -i s2-eth1 -w %s" % (mouse_goodput_file_path))
    sleep(1)
    start_iperf(net)
    sleep(3)
    random_generate_flows(net)
    sleep(7)
    # CLI( net )
    # sleep(20)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_topology()