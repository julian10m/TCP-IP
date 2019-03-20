import string
import threading 
import time
import random 
import queue

MAX_DATA_INTERVAL   = 2
SN_INIT             = 0
WINDOW_SIZE         = 9
MOD_SN_MAX          = WINDOW_SIZE + 1 

LENGTH_DATA = 10

data_generated  = threading.Event()
timer_expired   = threading.Event()
received_ACK    = threading.Event()

packets_in_the_channel = []
q_data = queue.Queue()
q_ACKs = queue.LifoQueue()

# class Window():
#     def __init__(self, sn_init, sn_max, window_size):
#         self.window_size = window_size 
#         self.base = sn_init
#         self.nextseqnum = sn_init
#         self.sn_max  = sn_max

class Packet():
    def __init__(self, data, sn, chk):
        self.data = data
        self.sn   = sn
        self.chk  = chk    

def set_timer_event():
    # print("Timer expired!!!")
    timer_expired.set()

def generate_data():
    for i in range(2*WINDOW_SIZE):
        d = ''.join(random.choices(string.ascii_uppercase + string.digits, k=LENGTH_DATA))
        time.sleep(0.5)
        q_data.put(d)
    time.sleep(5)
def generate_ACKs():
    for i in range(10):
        time.sleep(1.67)
        q_ACKs.put(Packet(None, i+1, None))

def print_status():
    while True:
        print(q_data.qsize(), q_ACKs.qsize())
        time.sleep(0.5)

class Sender_t(threading.Thread):
    def __init__(self, name, sn_init, mod_sn_max, window_size):
        threading.Thread.__init__(self)
        self.name = name
        self.window_size = window_size 
        self.base = sn_init
        self.nextseqnum = sn_init
        self.mod_sn_max  = mod_sn_max
        print("sn_max = {}".format(mod_sn_max))
    def run(self):
        Sender_t.sender_process(self)

    def make_seg(self, d, sn, chk):
        return Packet(d, sn, chk)    

    def read_ACK(self, ack):
        return ack.sn

    def sender_process(self):
        while True:
            # event = (event_sender.wait(3)
            if not q_data.empty():
                # if self.nextseqnum in [allowed_sn % self.mod_sn_max for allowed_sn in range(self.base, self.base+self.window_size)]:
                if ((self.nextseqnum < self.base+self.window_size) and (self.nextseqnum != (self.base+self.window_size) % self.mod_sn_max)):
                    d = q_data.get()
                    packets_in_the_channel.append(self.make_seg(d, self.nextseqnum, 0))
                    print("Packet sent: data={}, base = {} , seqnum = {}".format(d, self.base, self.nextseqnum), end=" ")
                    if self.base == self.nextseqnum:
                        print("start_timer()", end=" ")
                        timer = threading.Timer(4, set_timer_event)
                        timer.start()
                    self.nextseqnum = (self.nextseqnum + 1) % self.mod_sn_max
                    print("nextseqnum = {}, base+m={}".format(self.nextseqnum, (self.base+self.window_size) % self.mod_sn_max ))

            if timer_expired.is_set():
                timer = threading.Timer(4, set_timer_event)
                timer_expired.clear()
                timer.start()
                for seqnum in range(self.base, self.nextseqnum):
                    seqnum = seqnum % self.mod_sn_max
                    if self.nextseqnum == seqnum:
                        break                    
                    print("Timer expired!!! Resending seqnum {}".format(seqnum))
                print(50*"*", "Restarted Timer")

            if not q_ACKs.empty():
                ACK = q_ACKs.get()
                if random.uniform(0, 1) < 0.95:
                    base_temp = self.read_ACK(ACK)
                    print("ACK = {}".format(base_temp))
                    if base_temp in [expected_base % self.mod_sn_max for expected_base in range(self.base+1, self.nextseqnum+self.window_size+1)] and base_temp:
                        self.base = base_temp      
                        print("Base updated! {}".format(self.base))
                        if self.base == self.nextseqnum:
                            print("{}, {}".format(self.base, self.nextseqnum))
                            timer.cancel()


sender_t = Sender_t("TCP sender", SN_INIT, MOD_SN_MAX, WINDOW_SIZE)
generate_data_t = threading.Thread(target=generate_data)
generate_ACKs_t = threading.Thread(target=generate_ACKs)
queues_status_t = threading.Thread(target=print_status)

sender_t.daemon = True
generate_ACKs.daemon = True
queues_status_t.daemon = True

sender_t.start()
generate_data_t.start()
generate_ACKs_t.start()
queues_status_t.start()
generate_data_t.join()
generate_ACKs_t.join()


# def generate_data():
    # for i in range(10):
        # if data_generated.is_set():
            # while(data_generated.is_set()):
                # time.sleep(1)
        # time.sleep(random.randrange(0, MAX_DATA_INTERVAL+1))
        # print("Packet generated: {}".format(i+1))
        # data_generated.set()
    # print("ended data")

# def window_controller(window):
#     while True:
#         if data_generated.is_set():
#             if window.nextseqnum < ((window.base+window.window_size) % window.sn_max):
#                 # sndseg[nextseqnum] = make_seg(seqnum, d, chk)
#                 # to_CR(sndseg[nextseqnum])
#                 print("Packet sent: seqnum = {}".format(window.nextseqnum), end=" ")
#                 if window.base == window.nextseqnum:
#                     print("start_timer()", end=" ")
#                     timer = threading.Timer(1, set_timer_event)
#                     timer.start()
#                 window.nextseqnum = (window.nextseqnum + 1) % window.sn_max
#                 print("nextseqnum = {}, base+m={}".format(window.nextseqnum, (window.base+window.window_size) % window.sn_max))
#             else:
#                 print("refuse_data()")
#             data_generated.clear()

# window=Window(0, 5, 4)

# generate_data_t     = threading.Thread(target=generate_data)
# window_controller_t = threading.Thread(target=window_controller, args=(window,), daemon = True)


# generate_data_t.start()
# window_controller_t.start()

# generate_data_t.join()


