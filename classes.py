import logging
logging.basicConfig(level=logging.INFO)
l=logging.getLogger(__name__)
from scapy.all import *
import numpy as np
import base64

FILE='data/arbitrage.pcap'

class Packet:
    """extract useful from scapy packets and keep as attributes"""
    def __init__(self, packet):
        self.payload_bytes=bytes(packet[UDP].payload)
        self.payload=self.payload_bytes.decode()
        self.time=packet.time # float, we don't probably want datetime conversion
        self.src=packet[IP].src
        t=self.payload.split()
        self.symbol=t[1]
        self.seq=int(t[3])
        self.price=t[5]

class Parser:
    """Read pcap, generate array of packets"""
    def __init__(self, file):
        self.packets=[] 
        self.malformeds=[]
        self.senders=set()
        errors=0
        ok=0
        scapy_cap=rdpcap(file)
        for p in scapy_cap:
            try:
                pkt=Packet(p)
                self.packets.append(pkt)
                self.senders.add(p[IP].src)
                ok+=1
            except Exception as e:
                l.info(f"malformed packet from {p[IP].src}")
                l.info(f"While parsing: {e}, payload={p[UDP].payload}")
                self.malformeds.append(p)
                errors+=1
        l.info(f"parsed {file}, {ok} good packets, {errors} malformed")
        l.info(f"Senders: {self.senders}")

class DataPoint():
    """Represents a single message (all packets from sender)"""
    def __init__(self):
        self.seqno=None
        self.price={}
        self.time={}
        self.symbol={} 
        self.duplicates=[]
        self.senders=set()
    
    def addpacket(self,pkt):
        if type(self.seqno) != type(None) and self.seqno!=pkt.seq:
            l.warning(f"Trying to add packet with seqno {pkt.seq} to Datapoint {self.seqno}")
            raise ValueError(f"Trying to add packet with seqno {pkt.seq} to Datapoint {self.seqno}")
        sender=pkt.src 
        if sender in self.senders:
            self.duplicates.append(pkt) 
            return 
        self.price[sender]=pkt.price 
        self.seqno=pkt.seq 
        self.time[sender]=pkt.time 
        self.symbol[sender]=pkt.symbol 
        self.senders.add(sender)



    def makestats(self, senders):
        """Generate sender statistics. Needs list of senders to detect missing data"""
        
        class Stats: pass 
        self.stats=Stats()

        # 1. self.stats.times - for each sender
        mintime=min(self.time.values()) 
        self.stats.time=self.time.copy() 
        for t in self.stats.time:
            self.stats.time[t]-=mintime 
        # 2. missing data
        self.stats.missing=set(senders) - set(self.senders)
        # 3. Consensus
        self.stats.consensus=[] 
        if len(set(self.price.values()))>1:
            self.stats.consensus.append(self.price) 
        if len(set(self.symbol.values()))>1:
            self.stats.consensus.append(self.symbol)
        # 4. jitter (as abs timedelta from mean)
        self.stats.meantime=np.mean(np.fromiter(self.time.values(), dtype=float))  
        self.stats.jitter={} 
        for s in self.time:
            self.stats.jitter[s]=abs(self.time[s]-self.stats.meantime)
        
        

    
    @classmethod 
    def fromlist(cls, packets):
        """Return datapoints from list of packets""" 
        result={}
        for p in packets:
            dp=result.get(p.seq,DataPoint()) 
            dp.addpacket(p) 
            result[p.seq]=dp 
        l.info(f"Generated {len(result.keys())} datapoints")
        return result


class Sender:
    def __init__(self):
        self.missing=0
        self.malformed=0
        self.accdelay=0
        self.maxjitter=0 
        self.avgjitter=0
        self.score=0
    pass 

class SenderMaker:
    def __init__(self, datapoints, parser):
        self.senders={}
        self.charts={}
        for s in parser.senders:
            self.senders[s]=Sender()
            self.senders[s].addr=s
        self.datapoints=datapoints 
        self.parser=parser

    def _packeterrors(self):
        for s in self.senders.values():
            s.missing=0
            s.malformed=0
        for d in self.datapoints.values():
            for s in d.stats.missing:
                l.info(f"packeterrors s={s}")
                self.senders[s].missing+=1 
        for p in self.parser.malformeds:
            self.senders[p[IP].src].malformed+=1 
        
    def _latency(self):
        for s in self.senders.values():
            s.accdelay=0
        for f in self.datapoints.values():
            for s in f.stats.time:
                self.senders[s].accdelay+=f.stats.time.get(s,0)    
        l.info(f"in _latency_: {[(x.addr, x.accdelay) for x in self.senders.values()]}")
       # for s in self.senders:
       #     self.senders[s].meantimediff=self.senders[s].meantimediff/len(self.datapoints)

    def _jitter(self):
        for s in self.senders:
            times=np.array([ x.stats.time.get(s,None) for x in self.datapoints.values()] , dtype=float)
            offsets=[ a - b for a,b in zip(times[:-1], times[1:])] 
            self.senders[s].avgjitter=np.nanmean(offsets)
            self.senders[s].maxjitter=max(np.abs(offsets))

    def makestats(self):
        self.senderlist=list(sorted(self.senders.values(), key=lambda x: x.addr))
        for f in [self._packeterrors, self._latency, self._jitter]:
            f()
        

    def _maketimechart(self):
        y_pos=np.arange(len(self.senders))
        fig,ax=plt.subplots()
        #bar_width=0.35
        data=list(map(lambda x: x.accdelay,self.senderlist))
        names=list(map(lambda x: x.addr,self.senderlist))
        plt.barh(y_pos, data, align='center')
        plt.xlim((min(data), max(data)))
        plt.yticks(y_pos, names)
        plt.title('Accumulated delay from first packet')
        t=tempfile.TemporaryFile()
        fig.savefig(t, bbox_inches='tight', transparent=True)
        t.seek(0)
        encdata=base64.b64encode(t.read())
        return f"data:image/png;base64,{encdata.decode()}"

    def _makeavgjitterchart(self):
        y_pos=np.arange(len(self.senders))
        fig,ax=plt.subplots()
        #bar_width=0.35
        data=list(map(lambda x: x.avgjitter,self.senderlist))
        names=list(map(lambda x: x.addr,self.senderlist))
        plt.barh(y_pos, data, align='center')
        plt.xlim((min(data), max(data)))
        plt.yticks(y_pos, names)
        plt.title('Average Jitter')
        t=tempfile.TemporaryFile()
        fig.savefig(t, bbox_inches='tight', transparent=True)
        t.seek(0)
        encdata=base64.b64encode(t.read())
        return f"data:image/png;base64,{encdata.decode()}"


    def _makemaxjitterchart(self):
        y_pos=np.arange(len(self.senders))
        fig,ax=plt.subplots()
        #bar_width=0.35
        data=list(map(lambda x: x.maxjitter,self.senderlist))
        names=list(map(lambda x: x.addr,self.senderlist))
        plt.barh(y_pos, data, align='center')
        plt.xlim((min(data), max(data)))
        plt.yticks(y_pos, names)
        plt.title('Average Jitter')
        t=tempfile.TemporaryFile()
        fig.savefig(t, bbox_inches='tight', transparent=True)
        t.seek(0)
        encdata=base64.b64encode(t.read())
        return f"data:image/png;base64,{encdata.decode()}"



    def makecharts(self):
        
        self.charts={} 
        for a,b in[('Avg Jitter', self._makeavgjitterchart),
                ('Max Jitter', self._makemaxjitterchart),
                ('Packet delay', self._maketimechart)
        ]:
            l.info(f"Making chart {a}")
            self.charts[a]=b()
        plt.close()

    def score(self):
        """ Score senders. Scoring rules:
    - lost packet: -5,
    - malformed packet: -2
    - delays: 0 for best, -5 for next
    - max jitter: 0 for best, -4 for next
    - avg jitter: 0 for best, -5 for next
            """
        l.info("in score")
        
        self.makestats()
        self.makecharts()
        l.info(f"{self.senders}")
        #for s in self.senders:
        #    l.info(f"{s.__dict__}")
        delayorder=sorted(self.senderlist, key=lambda x: x.accdelay)
        avgjitterorder=sorted(self.senderlist, key=lambda x: x.avgjitter)
        maxjitterorder=sorted(self.senderlist, key=lambda x: x.maxjitter)
        for s in self.senderlist:
            missingscore=s.missing*-5
            s.score+=s.missing*-5
            l.info(f"Scorer {s.addr}, missing score {missingscore}, now {s.score}")
            malformedscore=s.malformed*-1
            s.score+=malformedscore
            l.info(f"Scorer {s.addr}, malformed score {malformedscore}, now {s.score}")
        for i,s in enumerate(delayorder):
            delayscore=i*-5
            s.score+=delayscore
            l.info(f"Scorer {s.addr}, delay order {i}, score {s.score}")
        for i,s in enumerate(avgjitterorder):
            ajscore=i*-4
            s.score+=ajscore
            l.info(f"Scorer {s.addr}, aj order {i}, ajscore {ajscore}, score {s.score}")
            
        for i,s in enumerate(maxjitterorder):
            mjscore=i*-5
            s.score+=mjscore
            l.info(f"Scorer {s.addr}, mj order {i}, mjscore {mjscore}, score {s.score}")

        





    

if __name__=='__main__':
    p=Parser(FILE) 
    datapoints=DataPoint.fromlist(p.packets)
    for d in datapoints.values():
        d.makestats(p.senders)
    sm=SenderMaker(datapoints, p)
    sm.score()




