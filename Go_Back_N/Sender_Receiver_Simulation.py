import string
import threading 
import time
import random 
import queue
from pprint import pprint
import os

WINDOW_SIZE = 9
MOD_SN_MAX  = WINDOW_SIZE + 1 

SN_INIT         = 0
base            = SN_INIT
nextseqnum      = SN_INIT
extpectedseqnum = SN_INIT

unacked_packets         = [None for _ in range(MOD_SN_MAX)]
packets_in_the_channel  = queue.Queue()
q_data                  = queue.Queue()
q_ACKs                  = queue.Queue()
q_received_data         = queue.Queue()

RTT_MU      = 300/1000
RTT_SIGMA   = 30/1000
RTT_0       = 3*RTT_MU

DELTA_T_ACKS    = 1.7
DELTA_T_DATA    = 0.5
DELTA_T_PRINT   = 0.5

Q_ACKs_SIM  = 5
Q_DATA_SIM  = 2*WINDOW_SIZE

LENGTH_DATA = 10

start_timer         = threading.Event()
update_timer_status = threading.Event()
stop_timer          = threading.Event()
updated_window      = threading.Event()

class Packet():
    def __init__(self, data, sn, chk, tmstp):
        self.data   = data
        self.sn     = sn
        self.chk    = chk    
        self.tmstp  = tmstp 

def retransmit_packets():
    t_now = time.time()
    print("\tResending seqnum :", end =" ")
    for seqnum in range(base, base+WINDOW_SIZE):
        seqnum = seqnum % MOD_SN_MAX
        if nextseqnum == seqnum:
            break
        unacked_packets[seqnum].tmstp = t_now
        packets_in_the_channel.put(unacked_packets[seqnum])
        print("{}, ".format(seqnum), end=" ")
    print("")

def set_timer_event():
    start_timer.set()
    update_timer_status.set()

def print_to_file(filename, data):
    with open(filename,"a") as f:
        print(data, file=f)

def window_controller():
    while True:
        data = q_data.get()
        if data is None:
            break
        global nextseqnum
        while not ((nextseqnum < base+WINDOW_SIZE) and (nextseqnum != (base+WINDOW_SIZE) % MOD_SN_MAX)):
            print("waiting")
            updated_window.wait()
        updated_window.clear()
        print_to_file("sdr_data.txt", data)
        unacked_packets[nextseqnum] = Packet(data, nextseqnum, 0, time.time())
        packets_in_the_channel.put(unacked_packets[nextseqnum])
        print("Packet sent: base = {} , seqnum = {}".format(base, nextseqnum))
        # print("Packet sent: base = {} , seqnum = {}".format(base, nextseqnum), end=" ")
        # print("Packet sent: data={}, base = {} , seqnum = {}".format(d, base, nextseqnum), end=" ")
        # pprint(unacked_packets)
        # for ind,packet in enumerate(unacked_packets):
            # if packet!=None:
                # print(ind, packet[0], packet[1])
                # print(ind, packet.sn, packet.data)
        if base == nextseqnum:
            print("---> Timer signalling", end=" ")
            start_timer.set()
        nextseqnum = (nextseqnum + 1) % MOD_SN_MAX
        print("nextseqnum = {}, base+m={}".format(nextseqnum, (base+WINDOW_SIZE) % MOD_SN_MAX))

def timer_controller():
    timer = threading.Timer(RTT_0, set_timer_event)
    while True:
        # print("Timer Alive?", timer.is_alive())
        if not timer.is_alive():
            print("------> Waiting for Timer signalling")
            start_timer.wait()
            print(50*"*", "Starting Timer")
            timer = threading.Timer(RTT_0, set_timer_event)
            timer.start()
            start_timer.clear()
        while True:
            print("------> Waiting for Timer Update event")
            update_timer_status.wait()
            update_timer_status.clear()
            if not timer.is_alive():
                print("------> Timer has expired!!")
                retransmit_packets()
                # print(20*"*", "------> Restarting Timer")
                break
            if stop_timer.is_set():
                timer.cancel()
                stop_timer.clear()
                print("------> Timer has been stopped!!")
                # print("Timer Alive?", timer.is_alive())
                break
            timer.cancel()
            global base
            t_base = unacked_packets[base].tmstp
            delta_RTT0 = RTT_0 + t_base - time.time()
            print("Timer readjusted! ---> delta_RTT0 = {0:.4f}".format(delta_RTT0))
            timer = threading.Timer(delta_RTT0, set_timer_event)
            timer.start()
            
def ACKs_controller():
    while True:
            ACK = q_ACKs.get()
            time.sleep(random.gauss(RTT_MU, RTT_SIGMA))
            if random.uniform(0, 1) > 0.75:
                print("--> Ack delayed!")
                time.sleep(3*RTT_MU)
            # if random.uniform(0, 1) < 0.95:
            base_temp = ACK.sn
            print("ACK = {}".format(base_temp))
            global base
            if base_temp in [expected_base % MOD_SN_MAX for expected_base in range(base+1, base+WINDOW_SIZE+1)]:
                for ind in [ind % MOD_SN_MAX for ind in range(base, base+WINDOW_SIZE)]:
                    if ind == base_temp:
                        break
                    unacked_packets[ind] = None 
                # pprint(unacked_packets)
                base = base_temp      
                print("Base updated! {}".format(base))
                updated_window.set()
                if base == nextseqnum:
                    print("---> Stopping signalling")
                    stop_timer.set()
                update_timer_status.set()


def generate_ACKs():
    for i in range(Q_ACKs_SIM):
        time.sleep(DELTA_T_ACKS)
        q_ACKs.put(Packet(None, i+1, None, time.time()))

def generate_data():
    for i in range(Q_DATA_SIM):
        d = ''.join(random.choices(string.ascii_uppercase + string.digits, k=LENGTH_DATA))
        time.sleep(DELTA_T_DATA)
        q_data.put(d)
    q_data.put(None)
    time.sleep(20)
    for t in range(3,0,-1):
        print("Shutting down in ...{}s".format(t))
        time.sleep(1)
    print("Finished Simulation")

def print_status():
    old = "0 0"
    while True:
        to_print = "{} {}".format(q_data.qsize(), q_ACKs.qsize())
        if old!=to_print:
            print(to_print)
        time.sleep(DELTA_T_PRINT)

def is_corrupt(packet):
    return False
    # if random.uniform(0, 1) < 0.95:    
        # return False
    # return True

def receiver_controller():
    while True:
        packet = packets_in_the_channel.get()
        time.sleep(random.gauss(RTT_MU, RTT_SIGMA))
        if not is_corrupt(packet):
            global extpectedseqnum
            if extpectedseqnum == packet.sn:
                data = packet.data
                q_received_data.put(data)
                print_to_file("rvr_data.txt", data)
                print("Packet received!! ---> seqnum = {}".format(extpectedseqnum))
                extpectedseqnum = (extpectedseqnum + 1) % MOD_SN_MAX
        q_ACKs.put(Packet(None, extpectedseqnum, None, time.time()))

os.remove("sdr_data.txt")
os.remove("rvr_data.txt")

generate_data_t = threading.Thread(target=generate_data)
window_controller_t = threading.Thread(target=window_controller)
timer_controller_t  = threading.Thread(target=timer_controller)
ACKs_controller_t   = threading.Thread(target=ACKs_controller)

receiver_controller_t = threading.Thread(target=receiver_controller)
# generate_ACKs_t = threading.Thread(target=generate_ACKs)

queues_status_t = threading.Thread(target=print_status)

queues_status_t.daemon      = True
window_controller_t.daemon  = True
timer_controller_t.daemon   = True
ACKs_controller_t.daemon    = True
receiver_controller_t.daemon = True

generate_data_t.start()
window_controller_t.start()
timer_controller_t.start()
ACKs_controller_t.start()

receiver_controller_t.start()
# generate_ACKs_t.start()

queues_status_t.start()

generate_data_t.join()

# receiver_controller_t.join()
# generate_ACKs_t.join()
