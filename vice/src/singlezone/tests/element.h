
#ifndef SINGLEZONE_TESTS_ELEMENT_H 
#define SINGLEZONE_TESTS_ELEMENT_H 

#ifdef __cplusplus 
extern "C" { 
#endif /* __cplusplus */ 

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
 * source: element.c 
 */ 
extern unsigned short quiescence_test_update_element_mass(SINGLEZONE *sz); 

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
 * source: element.c 
 */ 
extern unsigned short quiescence_test_onH(SINGLEZONE *sz); 

#ifdef __cplusplus 
} 
#endif /* __cplusplus */ 

#endif /* SINGLEZONE_TESTS_ELEMENT_H */ 
