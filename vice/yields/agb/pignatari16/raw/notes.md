# NuGrid Yields

## Data Tables
- From ritter+18, we download the table `element_yield_table_MESAonly_fryer12_delay_total.txt` in the database at (doi: 10.11570/18.0002). This is the core table.
- From Battino et al. 2019, the supplamentary data file stz2185_SupplementalFile
- From Battino et al. (2021), there is no directly published data. This study only affects masses of Msun=2, 3 at the metallicity Z=0.001

R+18 is a complete update of P+16, so we should only directly use this data. The P16 data is included here in case of comparison, but R+18 also extends the data to a larger grid. 
The work by Battino et al+ updates the Ne22(alpha) reaction rate (see Battino et al. 2022).


## Misc
I have verified that the Ritter tables do have the same AGB yields (and similar to adding up the isotopes) and have recalculated the yields for a few stars on Astrohub to verify the data. 
Battino yields would need recalculated :(.

We also have the Grevese & Noels (1993) abundance scale in `gn93.txt`
