import string
import threading 
import time
import random 
import queue
from pprint import pprint

MAX_DATA_INTERVAL   = 2
SN_INIT             = 0
WINDOW_SIZE         = 9
MOD_SN_MAX          = WINDOW_SIZE + 1 
RTT_0 = 10
LENGTH_DATA = 10

base = SN_INIT
nextseqnum = SN_INIT
packets_in_the_channel = [None for _ in range(MOD_SN_MAX)]
q_data = queue.Queue()
q_ACKs = queue.LifoQueue()

start_timer         = threading.Event()
update_timer_status = threading.Event()
stop_timer          = threading.Event()
updated_window      = threading.Event()

DELTA_T_ACKS    = 1.7
DELTA_T_DATA    = 0.5
DELTA_T_PRINT   = 0.5

Q_ACKs_SIM  = 5
Q_DATA_SIM  = 2*WINDOW_SIZE

class Packet():
    def __init__(self, data, sn, chk):
        self.data = data
        self.sn   = sn
        self.chk  = chk    

def make_seg(d, sn, chk):
    return Packet(d, sn, chk)    

def read_ACK(ack):
    return ack.sn

def retransmit_packets():
    t_now = time.time()
    print("\tResending seqnum :", end =" ")
    for seqnum in range(base, base+WINDOW_SIZE):
        seqnum = seqnum % MOD_SN_MAX
        if nextseqnum == seqnum:
            break
        packets_in_the_channel[seqnum][1] = t_now
        print("{}, ".format(seqnum), end=" ")
    print("")

def set_timer_event():
    start_timer.set()
    update_timer_status.set()

def window_controller():
    while True:
        d = q_data.get()
        if d is None:
            break
        global nextseqnum
        while not ((nextseqnum < base+WINDOW_SIZE) and (nextseqnum != (base+WINDOW_SIZE) % MOD_SN_MAX)):
            print("waiting")
            updated_window.wait()
        updated_window.clear()    
        packets_in_the_channel[nextseqnum] = [make_seg(d, nextseqnum, 0), time.time()]
        print("Packet sent: base = {} , seqnum = {}".format(base, nextseqnum))
        # print("Packet sent: base = {} , seqnum = {}".format(base, nextseqnum), end=" ")
        # print("Packet sent: data={}, base = {} , seqnum = {}".format(d, base, nextseqnum), end=" ")
        # pprint(packets_in_the_channel)
        # for ind,packet in enumerate(packets_in_the_channel):
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
            t_base = packets_in_the_channel[base][1]
            delta_RTT0 = RTT_0 + t_base - time.time()
            print("Timer readjusted! ---> delta_RTT0 = {}".format(delta_RTT0))
            timer = threading.Timer(delta_RTT0, set_timer_event)
            timer.start()
            
def ACKs_controller():
    while True:
            ACK = q_ACKs.get()
            # if random.uniform(0, 1) < 0.95:
            base_temp = read_ACK(ACK)
            print("ACK = {}".format(base_temp))
            global base
            if base_temp in [expected_base % MOD_SN_MAX for expected_base in range(base+1, nextseqnum+WINDOW_SIZE+1)]:
                for ind in [ind % MOD_SN_MAX for ind in range(base, base+WINDOW_SIZE)]:
                    if ind == base_temp:
                        break
                    packets_in_the_channel[ind] = None 
                # pprint(packets_in_the_channel)
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
        q_ACKs.put(Packet(None, i+1, None))

def generate_data():
    for i in range(Q_DATA_SIM):
        d = ''.join(random.choices(string.ascii_uppercase + string.digits, k=LENGTH_DATA))
        time.sleep(DELTA_T_DATA)
        q_data.put(d)
    q_data.put(None)
    time.sleep(10)

def print_status():
    old = "0 0"
    while True:
        to_print = "{} {}".format(q_data.qsize(), q_ACKs.qsize())
        if old!=to_print:
            print(to_print)
        time.sleep(DELTA_T_PRINT)

window_controller_t = threading.Thread(target=window_controller)
timer_controller_t  = threading.Thread(target=timer_controller)
ACKs_controller_t   = threading.Thread(target=ACKs_controller)

generate_data_t = threading.Thread(target=generate_data)
generate_ACKs_t = threading.Thread(target=generate_ACKs)
queues_status_t = threading.Thread(target=print_status)

queues_status_t.daemon      = True
window_controller_t.daemon  = True
timer_controller_t.daemon   = True
ACKs_controller_t.daemon    = True

generate_data_t.start()
generate_ACKs_t.start()
queues_status_t.start()
window_controller_t.start()
timer_controller_t.start()
ACKs_controller_t.start()


generate_data_t.join()
generate_ACKs_t.join()