#!/bin/bash

module load miniconda3/4.12.0-py39

# written like this so we can substitute the 
# name into the file for easier understanding

# first argument is filename
# second argument is the python call
echo "Submitting Job"
rm -f logs/$1.log

sbatch <<EOT
#!/bin/bash
#SBATCH --time=2:00:00
#SBATCH --ntasks=1
#SBATCH --mem=32gb
#SBATCH --job-name=$1
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --output=logs/$1
#SBATCH --account=PAS2232


set -x

cd $SLURM_SUBMIT_DIR
module load miniconda3/4.12.0-py39


python -c "
$2
" \$TMPDIR/

python \$SLURM_SUBMIT_DIR/osc/json_outputs.py \$TMPDIR/

cp -r -u \$TMPDIR/*.json \$SLURM_SUBMIT_DIR/output
cp -r -u \$TMPDIR/*.csv \$SLURM_SUBMIT_DIR/results

scontrol show job=\$SLURM_JOB_ID

EOT
