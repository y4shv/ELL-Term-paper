"""SC keeps every program-order pair."""
from graph import program_order, from_read_arrows


def graphs(events, fences, reads_from, write_order):
    arrows = (program_order(events) + reads_from + write_order
              + from_read_arrows(reads_from, write_order))
    
    return [arrows]
