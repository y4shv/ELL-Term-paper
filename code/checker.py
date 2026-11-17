from itertools import permutations, product

from tests import LITMUS, TARGET, EXPECTED, RANDOM_TESTS
import sc
import tso
import pso


MODELS = [("SC", sc), ("TSO", tso), ("PSO", pso)]


class Event:
    def __init__(self, kind, var, value=None, reg=None,
                 thread=None, index=None, label=None):
        self.kind = kind
        self.var = var
        self.value = value
        self.reg = reg
        self.thread = thread
        self.index = index
        self.label = label

    def __repr__(self):
        return self.label


def find_variables(test):
    var_list = set()

    for thread in test:
        for op in thread:
            if op[0] == "W":
                var_list.add(op[1])
            elif op[0] == "R":
                var_list.add(op[2])

    return sorted(var_list)


def make_label(cnt):
    label = ""
    while cnt >= 0:
        label = chr(ord("a") + cnt % 26) + label
        cnt = cnt // 26 - 1
    return label


def make_events(test):
    var_list = find_variables(test)
    events = []
    fences = []

    # Add the initial write for every variable before the program events.
    for var in var_list:
        events.append(Event("W", var, value=0, label="init_" + var))

    cnt = 0
    for tid, thread in enumerate(test):
        for pos, op in enumerate(thread):
            if op[0] == "W":
                _, var, val = op
                events.append(Event("W", var, value=val,
                                    thread=tid, index=pos,
                                    label=make_label(cnt)))
                cnt += 1

            elif op[0] == "R":
                _, reg, var = op
                events.append(Event("R", var, reg=reg,
                                    thread=tid, index=pos,
                                    label=make_label(cnt)))
                cnt += 1

            else:
                _, kind = op
                fences.append((tid, pos, kind))

    return events, fences, var_list


def has_cycle(nodes, arrows):
    indeg = {}
    adj = {}

    for node in nodes:
        indeg[node] = 0
        adj[node] = []

    for u, v in set(arrows):
        adj[u].append(v)
        indeg[v] += 1

    st = []
    for node in nodes:
        if indeg[node] == 0:
            st.append(node)

    cnt = 0
    while st:
        u = st.pop()
        cnt += 1

        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                st.append(v)

    return cnt != len(nodes)


def all_guesses(events, var_list):
    reads = [e for e in events if e.kind == "R"]

    writes = {}
    for var in var_list:
        writes[var] = [e for e in events if e.kind == "W" and e.var == var]

    read_opts = []
    for r in reads:
        read_opts.append(writes[r.var])

    write_opts = []
    for var in var_list:
        init = writes[var][0]
        other = writes[var][1:]

        arr = []
        for p in permutations(other):
            arr.append([init] + list(p))

        write_opts.append(arr)

    guesses = []
    for chosen in product(*read_opts):
        reads_from = list(zip(chosen, reads))

        for orders in product(*write_opts):
            write_order = []
            for order in orders:
                for i in range(len(order)):
                    for j in range(i + 1, len(order)):
                        write_order.append((order[i], order[j]))

            guesses.append((reads_from, write_order, orders))

    return guesses


def guess_is_possible(events, fences, model, guess):
    reads_from, write_order, _ = guess

    for arrows in model.graphs(events, fences, reads_from, write_order):
        if has_cycle(events, arrows):
            return False

    return True


def outcome_of(guess):
    reads_from, _, orders = guess

    reg_val = []
    for write, read in reads_from:
        reg_val.append((read.reg, write.value))

    # Sorting makes equivalent register outcomes have the same set representation.
    reg_val = tuple(sorted(reg_val))

    memory = []
    for order in orders:
        last = order[-1]
        memory.append((last.var, last.value))

    # var_list is sorted, so the final memory values are already in a fixed order.
    return reg_val, tuple(memory)


def check(test, model):
    events, fences, var_list = make_events(test)
    allowed = set()

    for guess in all_guesses(events, var_list):
        if guess_is_possible(events, fences, model, guess):
            allowed.add(outcome_of(guess))

    return allowed


def outcome_is_allowed(allowed, target):
    for registers, _ in allowed:
        vals = dict(registers)
        ok = True

        for reg, val in target.items():
            if vals[reg] != val:
                ok = False
                break

        if ok:
            return True

    return False


def run_litmus_tests():
    ok = True
    print("test outcome SC TSO PSO as expected?")

    for name, test in LITMUS.items():
        verdict = ""

        for _, model in MODELS:
            allowed = check(test, model)
            if outcome_is_allowed(allowed, TARGET[name]):
                verdict += "A"
            else:
                verdict += "F"

        match = (verdict == EXPECTED[name])
        if not match:
            ok = False

        print(f"{name:<12s} {str(tuple(TARGET[name].values())):<12s} "
              f"{verdict[0]:>3s} {verdict[1]:>3s} {verdict[2]:>3s}   "
              f"{'yes' if match else 'NO'}")

    return ok


def run_subset_check():
    progs = list(LITMUS.values()) + RANDOM_TESTS

    fail = 0
    sc_less = 0
    tso_less = 0

    for test in progs:
        a = check(test, sc)
        b = check(test, tso)
        c = check(test, pso)

        if not (a <= b and b <= c):
            fail += 1

        if a < b:
            sc_less += 1

        if b < c:
            tso_less += 1

    print(f"\nSubset check on {len(progs)} programs")
    print("  SC <= TSO <= PSO fails:            ", fail)
    print("  SC allows strictly less than TSO:  ", sc_less)
    print("  TSO allows strictly less than PSO: ", tso_less)

    return fail == 0


def print_candidates(name):
    test = LITMUS[name]
    events, fences, var_list = make_events(test)

    print(f"\nCandidate executions of {name}")
    print(f"  {'who each read reads from':<34s} {'(r0,r1)':<8s} "
          f"{'SC':>7s} {'TSO':>7s} {'PSO':>7s}")

    for guess in all_guesses(events, var_list):
        reads_from = guess[0]

        reads = []
        for write, read in reads_from:
            reads.append(f"{read.label} reads {write.label}")

        registers, _ = outcome_of(guess)
        vals = "(" + ", ".join(str(v) for _, v in registers) + ")"

        ans = []
        for _, model in MODELS:
            if guess_is_possible(events, fences, model, guess):
                ans.append("allowed")
            else:
                ans.append("cycle")

        print(f"  {', '.join(reads):<34s} {vals:<8s} "
              f"{ans[0]:>7s} {ans[1]:>7s} {ans[2]:>7s}")


def main():
    litmus_ok = run_litmus_tests()

    print_candidates("SB")
    print_candidates("MP")

    subset_ok = run_subset_check()

    ok = litmus_ok and subset_ok
    print("\nAll checks passed:", "yes" if ok else "NO")

    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)