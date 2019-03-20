# Par contre...a la place de forcer que les paquets soient envoyes quand le 
# programme commence, on considere le cas que, peut-etre, il n'y a pas des
# donnes pour le moment...alors, base = nextseqnum = 0 quand tout commence.
# A exception de ce petit changement, tout le reste se deroule dans la meme
# facon qu'avant.

# m: Taille de la fenetre, elle est donee
m = M

# |SN| >= m+1 --> SNmin = m+1. Alors... SN ={0,...,m} verifie! Finalement MOD_MAX_SN = m+1
# Attention! En general il y a une condition sur SN ---> |SN| = 2^n, ou n = #bits...
# Alors on va considerer que m est deja une valeur qu'on peut calculer comme m = (2^n)-1 
MOD_MAX_SN = m+1

# base: Premier Segment Non Acquitte
base = 0
# nextseqnum: Prochain Segment A Emettre
nextseqnum = 0

while(True):

	# On attend un evenement:
	#     - ACK recu?
	#     - Data de la couche applicative qu'arrive?
	#     - Timeout?	
	wait_event()

	# Si on recoi un ACK...Si le segment n'a pas des erreurs et si l'ACK a une valeur
	# entre ceux qui etaient attendus, on actualise la fenetre. S'il n'y reste pas des
	# paquets dans le canal, on arrete le timer. S'il y en a encore, on mettre a jour le
	# timer (il devient le timer du segment qui est maintenant a la base).
	if event == from_CR(s):
		if not_corrupt(s):
			base_temp = get_ack(s)
			if base_temp in [expected_base % MOD_MAX_SN for expected_base in range(base, base+m)]:
				base = base_temp
				if base == nextseqnum:
					stop_timer()
				else:
					adjust_timer()

	# Si la couche applicative envoie de data vers la couche transport,
	# si la fenetre n'est pas rempli, on envoie le segment a la couche
	# reseau. S'il n'y a avait pas des paquets dans le canal, on doit 
	# commencer le timer, et on fini par mettre a jour quel sera le NumSeq
	# d'un nouveau paquet. Si, par contre, la fenetre est rempli, on refuse
	# d'envoyer plus d'info.   
	elif event == from_CA(d):
		if ((nextseqnum < (base+m)) and (nextseqnum != (base+m) % MOD_MAX_SN)):
			sndseg[nextseqnum] = make_seg(seqnum, d, chk)
			to_CR(sndseg[nextseqnum])
			if base == nextseqnum:
				start_timer()
			nextseqnum = (nextseqnum + 1) % MAX_SN
		else:
			refuse_data(d)

	# Si il y a un timeout, on doit renvoyer tous les paquets qui etaient dans
	# le canal. Alors, renvoyer les paquets entre le premier SN non aquitee et 
	# lequel nous allons envoyer une fois qu'il y a de data qui arrive. Il est
	# important de remarque que nous devons recommencer le timer dans ce cas la
	# ...il y a avait expire! alors...bien sur :D 
	elif event == timeout():
		start_timer()
		for seqnum in range(base, base+m):
			seqnum = seqnum % (m+1)
			if nextseqnum == seqnum:
				break
			to_CR(sndseg[seqnum])

