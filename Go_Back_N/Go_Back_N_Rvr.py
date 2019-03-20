# Go Back N - Receiver
# Detail sur Python: for x in range(a,a+N) alors x prends la valeur "a" quand le for 
# commence, et la valaeur "a+N-1" a la fin. Autrement dit, a+N n'est pas compris! 

# Le recepteur doit connaitre que SN={???}. On avait vu que |SN| >= m+1 --> SNmin = m+1
# Alors... SN ={0,...,m} c'etait une possibilite. Finalement MOD_MAX_SN = m+1
# Attention! En general il y a une condition sur SN ---> |SN| = 2^n, ou n = #bits...
# Alors on va considerer que m est deja une valeur qu'on peut calculer comme m = (2^n)-1 
MOD_MAX_SN = m+1

# Segment Attendu
expectedseqnum = 0

while(True):

	# On attend un evenement:
	#  - Arrivee d'un paquet
	wait_event()

	# Si un paquet arrive, si le segment n'a pas des erreurs et si le SN est lequel on
	# attendait, on envoie le data vers la couche applicative, et on met a jour le SN 
	# attendu dans le prochaine segment qui arrivera. Par contre, si le SN dans le segment
	# recu est different a lequel nous attendions ou si le segment a des erreurs, on 
	# ne change pas le SN attendu. Dans toutes les cas, onvoie un ACK la valeur de le
	# SN attendu, qui peut ou pas avoir etre modifie, pour laisser savoir le sender le
	# segment que nous attendons.
	if event == from_CR(s):
		if not_corrupt(s):
			if extpectedseqnum == get_seqnum(s):
				to_CA(s.data)
				extpectedseqnum = (extpectedseqnum + 1) % MOD_MAX_SN
		sok.ACK = extpectedseqnum
		to_CR(sok)

