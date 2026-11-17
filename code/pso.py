"""PSO relaxes W -> R and W -> W."""
from graph import (preserved_program_order, fence_arrows, external_reads_from,
                   from_read_arrows, same_address_arrows)

KEPT = {"RR", "RW"}


def graphs(events, fences, reads_from, write_order):
    global_arrows = (preserved_program_order(events, KEPT)
                     + fence_arrows(events, fences)
                     + external_reads_from(reads_from)
                     + write_order
                     + from_read_arrows(reads_from, write_order))
    
    return [global_arrows, same_address_arrows(events, reads_from, write_order)]
