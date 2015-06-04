#!/bin/sh
export PATH=/curc/slurm/slurm/current/bin:${PATH}
export LD_LIBRARY_PATH=/curc/slurm/slurm/current/lib:${LD_LIBRARY_PATH}
export MANPATH=/curc/slurm/slurm/current/share/man:${MANPATH}
export SLURM_ROOT=/curc/slurm/slurm/current
export I_MPI_PMI_LIBRARY=/curc/slurm/slurm/current/lib/libpmi.so