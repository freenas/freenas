: logo ( x y -- ) \ "FreeNAS" logo in B/W (13 rows x 24 columns)

	5 + swap 6 + swap

	2dup at-xy ."  ______                " 1+
	2dup at-xy ." |  ____| __ ___  ___   " 1+
	2dup at-xy ." | |__ | '__/ _ \/ _ \  " 1+
	2dup at-xy ." |  __|| | |  __/  __/  " 1+
	2dup at-xy ." | |   | | |    |    |  " 1+
	2dup at-xy ." |_|   |_|  \___|\___|  " 1+
	2dup at-xy ."  _     _   __    _____ " 1+
	2dup at-xy ." | \   | | /  \  /  ___|" 1+
	2dup at-xy ." |  \  | |/ /\ \|  (__  " 1+
	2dup at-xy ." | |\\ | | |__| |\___ \ " 1+
	2dup at-xy ." | | \\| |  __  |____) |" 1+
	2dup at-xy ." | |  \  | |  | |      |" 1+
	     at-xy ." |_|   \_|_|  |_|_____/ "

	\ Put the cursor back at the bottom
	0 25 at-xy
;
