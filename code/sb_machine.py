"""Store-buffer simulation for SC, TSO and PSO.

Explores the possible instruction and buffer-drain steps, then compares the
final outcomes with checker.py.

SC   writes go straight to memory
TSO  only the oldest buffered store can drain
PSO  stores to different addresses may drain out of order

mfence waits for an empty buffer; stbar leaves a marker in the buffer.

Run: python3 sb_machine.py
"""
from checker import check, MODELS
from tests import LITMUS, RANDOM_TESTS

# Buffer entries: ("S", address, value) or an stbar marker ("B",)
# State: program counters, buffers, memory and register values
# Tuples let us store each state in a set.


def addresses_used(test):
    names = set()
    for thread in test:
        for instruction in thread:
            if instruction[0] == "W":
                names.add(instruction[1])
            elif instruction[0] == "R":
                names.add(instruction[2])
    return sorted(names)


def start_state(test):
    memory = []
    for address in addresses_used(test):
        memory.append((address, 0))         # every address starts at 0
    pcs = tuple(0 for _ in test)
    buffers = tuple(() for _ in test)       # empty buffers
    return (pcs, buffers, tuple(memory), ())


def write_to_memory(memory, address, value):
    """Copy memory and update one address."""
    as_dict = dict(memory)
    as_dict[address] = value
    return tuple(sorted(as_dict.items()))


def replace_item(items, index, new_item):
    """Copy a tuple with one item replaced."""
    return items[:index] + (new_item,) + items[index + 1:]


def may_drain(buffer, i, model):
    """Whether entry i can drain now."""
    entry = buffer[i]
    if entry[0] != "S":
        return False  # marker
    if model == "TSO":
        return i == 0  # FIFO
    # PSO: check older entries
    for older in buffer[:i]:
        if older[0] == "B":
            return False  # older stbar
        if older[1] == entry[1]:
            return False  # older store to the same address
    return True


def read_value(buffer, memory, address):
    """Read the newest matching store, or memory if there is none."""
    for entry in reversed(buffer):  # newest first
        if entry[0] == "S" and entry[1] == address:
            return entry[2]
    return dict(memory)[address]


def next_states(state, test, model):
    """Possible states after one step."""
    pcs, buffers, memory, regs = state
    result = []

    for t in range(len(test)):
        thread = test[t]
        buffer = buffers[t]

        # Thread t runs its next instruction
        if pcs[t] < len(thread):
            instruction = thread[pcs[t]]
            new_pcs = replace_item(pcs, t, pcs[t] + 1)

            if instruction[0] == "W":
                _, address, value = instruction
                if model == "SC":
                    # SC: straight to memory
                    new_memory = write_to_memory(memory, address, value)
                    result.append((new_pcs, buffers, new_memory, regs))
                else:
                    # add to its buffer
                    new_buffer = buffer + (("S", address, value),)
                    result.append((new_pcs, replace_item(buffers, t, new_buffer),
                                   memory, regs))

            elif instruction[0] == "R":
                _, register, address = instruction
                value = read_value(buffer, memory, address)
                new_regs = tuple(sorted(regs + ((register, value),)))
                result.append((new_pcs, buffers, memory, new_regs))

            else:                           # a fence
                _, kind = instruction
                if kind == "mfence":
                    # wait for an empty buffer
                    if len(buffer) == 0:
                        result.append((new_pcs, buffers, memory, regs))
                elif kind == "stbar":
                    if model == "PSO":
                        new_buffer = buffer + (("B",),)
                        result.append((new_pcs, replace_item(buffers, t, new_buffer),
                                       memory, regs))
                    else:
                        # SC and TSO already keep W -> W order
                        result.append((new_pcs, buffers, memory, regs))

        # Hardware drains an entry from buffer t
        if len(buffer) > 0 and buffer[0][0] == "B":
            # remove a marker at the front
            result.append((pcs, replace_item(buffers, t, buffer[1:]),
                           memory, regs))
        for i in range(len(buffer)):
            if may_drain(buffer, i, model):
                entry = buffer[i]
                new_buffer = buffer[:i] + buffer[i + 1:]
                new_memory = write_to_memory(memory, entry[1], entry[2])
                result.append((pcs, replace_item(buffers, t, new_buffer),
                               new_memory, regs))

    return result


def all_final_outcomes(test, model):
    """Explore step orders and collect final outcomes."""
    start = start_state(test)
    seen = {start}
    to_visit = [start]
    outcomes = set()

    while len(to_visit) > 0:
        state = to_visit.pop()
        pcs, buffers, memory, regs = state

        # All instructions done and buffers empty
        all_threads_done = all(pcs[t] == len(test[t]) for t in range(len(test)))
        all_buffers_empty = all(len(b) == 0 for b in buffers)
        if all_threads_done and all_buffers_empty:
            outcomes.add((regs, memory))

        for new_state in next_states(state, test, model):
            if new_state not in seen:
                seen.add(new_state)
                to_visit.append(new_state)

    return outcomes, len(seen)


def main():
    print("Store-buffer machine simulation, compared with checker.py")
    print("=" * 60)
    all_agree = True

    print("%-12s %-4s %8s %10s %10s  %s" % (
        "test", "model", "states", "machine", "checker", "same?"))
    for name, test in LITMUS.items():
        for model_name, model_file in MODELS:
            machine, state_count = all_final_outcomes(test, model_name)
            checker_result = check(test, model_file)
            same = (machine == checker_result)
            if not same:
                all_agree = False
            print("%-12s %-4s %8d %10d %10d  %s" % (
                name, model_name, state_count, len(machine),
                len(checker_result), "yes" if same else "NO"))

    differences = 0
    for test in RANDOM_TESTS:
        for model_name, model_file in MODELS:
            machine, _ = all_final_outcomes(test, model_name)
            if machine != check(test, model_file):
                differences += 1
    if differences > 0:
        all_agree = False
    print("\nRandom programs: %d, models per program: 3" % len(RANDOM_TESTS))
    print("  (program, model) pairs where machine and checker differ: %d"
          % differences)
    print("\nMachine and checker agree everywhere:", "yes" if all_agree else "NO")
    return all_agree


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
