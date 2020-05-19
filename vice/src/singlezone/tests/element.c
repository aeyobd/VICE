/* 
 * This file implements testing of the single-element time-evolution routines 
 * at element.h in the parent directory. 
 */ 

#include "../element.h" 
#include <math.h> 

/* 
 * Implements the quiescence test on the update_element_mass function in the 
 * parent directory by ensuring that each element's mass is equal to zero. 
 * 
 * Parameters 
 * ==========
 * sz: 		A pointer to the singlezone object to run the quiescence test on 
 * 
 * Returns 
 * =======
 * 1 on success, 0 on failure 
 * 
 * header: element.h 
 */ 
extern unsigned short quiescence_test_update_element_mass(SINGLEZONE *sz) { 

	unsigned short i, status = 1u; 
	for (i = 0u; i < (*sz).n_elements; i++) { 
		status &= (*(*sz).elements[i]).mass == 0; 
		if (!status) break; 
	} 
	return status; 

}


/* 
 * Implements the quiescence test on the onH function in the parent directory 
 * by ensuring that [X/H] = -infinity for each element. 
 * 
 * Parameters 
 * ==========
 * sz: 		A pointer to the singlezone object to run the quiescence test on 
 * 
 * Returns 
 * =======
 * 1 on success, 0 on failure 
 * 
 * header: element.h 
 */ 
extern unsigned short quiescence_test_onH(SINGLEZONE *sz) {

	unsigned short i, status = 1u; 
	for (i = 0u; i < (*sz).n_elements; i++) {
		status &= onH(*sz, *(*sz).elements[i]) == -INFINITY; 
		if (!status) break; 
	} 
	return status; 

}

