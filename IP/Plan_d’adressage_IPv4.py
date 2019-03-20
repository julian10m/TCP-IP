import math 
from random import shuffle
# from pprint import pprint

class SousReseau:
    def __init__(self, qIPs):
        self.qIPs = qIPs
        self.x = self.SousReseaux_PrefixLength(qIPs)
        self.seg = None
    def SousReseaux_PrefixLength(self, qIPs):
        return 32 - math.ceil(math.log2(qIPs))

#*********************************** Plan_d’adressage_IPv4 **********************************
#*********************************** Plan_d’adressage_IPv4 **********************************
#*********************************** Plan_d’adressage_IPv4 **********************************
#
# On considere que nous avons un Reseau dans le prefix ---> A.B.C.D/x et que l'on veut diviser
# a plusiers Sous-Reseaux (SR). En particulier N SRs.
#
# On va supposer qu'on connais #IPs/SR --> qIPs_SR = [v1, v2, ..., vi,..., vN]. Ou "vi" est 
# justement "#IPs/SRi". Merci de remarquer la "i" dans "SRi". 
#
# ATTENTION -- #IPs, pas #hotes ou #machines... ---> #IPs = #hotes + 1 (Reseaux) + 1 (Broadcast) 
# Quand dans le SR il n'y a pas deja un router, il faut compter une adresse IP additional!!
#
# RandomOrder = True/False.
#         - False ---> Ordre du SR plus grand au plus petit.
#        - True  ---> L'ordre dans lequel on prends les SRs change a chaque fois.
#
# Profitez! Si vous trouvez un erreur, dites moi! ---> Julian M. DEL FIORE: delfiore@unistra.fr
#

RandomOrder = False

qIPs_SR = [256, 177, 50, 4, 4, 4, 20]

if RandomOrder:
    shuffle(qIPs_SR)
else:
    qIPs_SR.sort(key=lambda x: x, reverse=True)    
    
SRs = []
for qIPs in qIPs_SR:
    SRs.append(SousReseau(qIPs))

x = 32 - math.ceil(math.log2(sum([2**(32-SR.x) for SR in SRs])))
# print("x" ,x)
Segs=[]
print (25*"*", "Sous Reseaux", 25*"*")
for SRi in SRs:
    print("SR: qIPs = %s --> /%s" % (SRi.qIPs, SRi.x))
    LenSeg = 1/2**(SRi.x-x)
    Pos = 0
    # print("LenSeg: ", LenSeg)
    while(1):
        overlap = False
        for Seg in Segs:
            # if (Pos+LenSeg > Seg[0] and Pos <= Seg[0]) or \
               # (Pos < Seg[1] and Pos+LenSeg >= Seg[1]) or \
               # (Pos >= Seg[0] and Pos+LenSeg <= Seg[1]):
            if max(Pos+LenSeg, Seg[1]) - min(Pos, Seg[0]) < LenSeg + (Seg[1] - Seg[0]): 
                overlap = True
                Pos += LenSeg
                break 
        if not overlap:
            # print(Pos, Pos+LenSeg)
            SRi.seg=(int(Pos*2**(32-x)), int((Pos+LenSeg)*2**(32-x)))
            # print(SRi.seg)
            Segs.append((Pos, Pos+LenSeg))
            # print("Segs", Segs)
            break

# Segs = [(xx*2**(32-x), yy*2**(32-x)) for (xx,yy) in Segs]
# print(Segs)        
print (25*"*", " Resultat", 25*"*")

if x<=8:
    print ("Reseau", "A.0.0.0/%s" % x)
elif 8<x<=16:
    print ("Reseau", "A.B.0.0/%s" % x)
elif 16<x<=24:
    print ("Reseau", "A.B.C.0/%s" % x)    
else:
    print ("Reseau", "A.B.C.D/%s" % x)
    
SRs.sort(key=lambda x: (x.seg[1], x.seg[0]))

for SRi in SRs:
    xx = SRi.seg[0]
    yy = SRi.seg[1]
    # print(xx, yy)

    if yy<=256 or xx==0:
        print("\t","A.B.C.%s/%s" % (xx,SRi.x))
    elif 256<yy<=2**16:
        DeltaC = int(math.floor(xx/256))
        DeltaD = xx - 256*DeltaC
        # print("DeltaD", DeltaD)
        print("\t","A.B.(C+%s).%s/%s" % (DeltaC, DeltaD,SRi.x))


