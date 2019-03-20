# Go Back N - Sender - Case: Infinies donnees
# Detail sur Python: for x in range(a,a+N) alors x prends la valeur "a" quand le for 
# commence, et la valaeur "a+N-1" a la fin. Autrement dit, a+N n'est pas compris! 

# m: Taille de la fenetre, elle est donee
m = M

# |SN| >= m+1 --> SNmin = m+1. Alors... SN ={0,...,m} verifie! Finalement MOD_MAX_SN = m+1
# Attention! En general il y a une condition sur SN ---> |SN| = 2^n, ou n = #bits...
# Alors on va considerer que m est deja une valeur qu'on peut calculer comme m = (2^n)-1 
MOD_MAX_SN = m+1

# base: Premier Segment Non Acquitte
base = 0

# On commence par envoyer une fenetre de messages. Attention! Le timer devrais
# etre demarre (start_timer()) des le sndseg[1] est envoye, et pas avant...mais
# on va considerer qu'il ne change rien si on le fait commencer un peu avant...
start_time()
for seqnum in range(base, base+m):
	sndseg[seqnum] = make_seg(seqnum, d, chk)
	to_CR(sndseg[seqnum])

# nextseqnum: Prochain Segment A Emettre
nextseqnum = m	

while(True):

	# On attend un evenement:
	#     - ACK recu?
	#     - Timeout?
	wait_event()

	# Si on recoi un ACK...Si le segment n'a pas des erreurs et si l'ACK a une valeur
	# entre ceux qui etaient attendus, on actualise la fenetre et on mettre a jour le
	# timer (il devient le timer du segment avec SN=base). En plus, comme il y a une
	# infinite des donnes, des qu'on actualise la fenetre, on peut envoyer des autres
	# segments, mais on ne renvoi pas ceux qui sont deja dans le canal. Par contre, si
	# le paquet a des erreurs ou c'est un ACK vieux, on ne le trait pas du tout...on 
	# attend l'arrive d'une autre ACK ou l'expiration du timer.
	if event == from_CR(s):
		if not_corrupt(s):
			base_temp = get_ack(s)
			if base_temp in [expected_base % MOD_MAX_SN for expected_base in range(base+1, base+m+1)]:
				base = base_temp
				adjust_timer()
				for seqnum in range(base, base+m):
					seqnum = seqnum % MOD_MAX_SN
					if not already_sent(sndseg[seqnum]):
						sndseg[seqnum] = make_seg(seqnum, d, chk)
						to_CR(sndseg[nextseqnum])

	# Si il y a un timeout...on doit renvoyer tous les paquets qui etaient dans le canal. 
	# Comme on supose qu'il y a une infinite des donnes, on va suposser que la fenetre 
	# etait deja rempli, et qu'on doit renvoyer m paquets. En plus, nous devons recommencer
	# le timer, parce qu'il avait expire
	elif event == timeout():
		start_timer()
		for seqnum in range(base, base+m):
			seqnum = seqnum % MOD_MAX_SN
			to_CR(sndseg[seqnum])

