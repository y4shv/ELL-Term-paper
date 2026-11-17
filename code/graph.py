"""Helpers for building order graphs."""

# Pairs restored by each fence
FENCE_RESTORES = {
    "mfence": {"RR", "RW", "WW", "WR"},
    "stbar": {"WW"},
}


def pair(a, b):
    return a.kind + b.kind


def program_order(events):
    pairs = []
    for a in events:
        for b in events:
            if a.thread is None or b.thread is None:
                continue  # initial writes have no thread
            if a.thread == b.thread and a.index < b.index:
                pairs.append((a, b))

    return pairs


def preserved_program_order(events, kept):
    arrows = []
    for a, b in program_order(events):
        if a.var != b.var:
            if pair(a, b) in kept:
                arrows.append((a, b))
        elif pair(a, b) != "WR":  # W -> R may get its value from the store buffer
            arrows.append((a, b))

    return arrows


def fence_arrows(events, fences):
    arrows = []
    for a, b in program_order(events):
        for tid, pos, kind in fences:
            between = (a.thread == tid and a.index < pos < b.index)
            if between and pair(a, b) in FENCE_RESTORES[kind]:
                arrows.append((a, b))

    return arrows


def external_reads_from(reads_from):
    return [(write, read) for write, read in reads_from
            if write.thread != read.thread]


def from_read_arrows(reads_from, write_order):
    arrows = []
    for write, read in reads_from:
        for first, later in write_order:
            if first is write:
                arrows.append((read, later))  # read before later writes

    return arrows


def same_address_arrows(events, reads_from, write_order):
    # Same-address program order, reads-from, write order and from-read
    same_po = [(a, b) for a, b in program_order(events)
               if a.var == b.var]

    return (same_po + reads_from + write_order
            + from_read_arrows(reads_from, write_order))
