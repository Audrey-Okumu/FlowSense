"""FlowSense rule-based adaptive signal controller (the "brain").

Used by simulation/run_flowsense.py. Rules (see choose()):
  - minimum green MIN_G s, maximum green MAX_G s, yellow always kept
  - any vehicle waiting more than STARVE s forces its phase next
  - switch early when the served road empties and another road has cars waiting
  - switch when another road's demand >= RATIO x the current demand + BIAS
Demand of a phase = stopped vehicles on its lanes + (waiting time / 10).
"""
import traci

MIN_G, MAX_G, YELLOW, STARVE, RATIO, BIAS = 8, 60, 3, 90, 2, 3


def choose(cur, t_in, demand, wait, min_g=MIN_G, max_g=MAX_G, starve=STARVE, ratio=RATIO, bias=BIAS):
    """Return the group to switch to, or None to keep the current green.
    demand / wait: dicts {group: value}. Pure function: used by SUMO runs AND the camera-input replay."""
    if t_in < min_g:
        return None
    oth = [g for g in demand if g != cur]
    if not oth:
        return None
    best = max(oth, key=lambda g: demand[g])
    db, dc = demand[best], demand[cur]
    starved = [(wait.get(g, 0), g) for g in oth if demand[g] > 0 and wait.get(g, 0) > starve]
    if starved:
        return max(starved)[1]
    if t_in >= max_g and db > 0:
        return best
    if dc == 0 and db > 0:
        return best
    if db >= ratio * dc + bias:
        return best
    return None


class Flow:
    def __init__(self, tls, min_g=MIN_G, max_g=MAX_G, starve=STARVE, ratio=RATIO, bias=BIAS):
        tl = traci.trafficlight; self.tls = tls
        self.p = dict(min_g=min_g, max_g=max_g, starve=starve, ratio=ratio, bias=bias)
        self.lanes = tl.getControlledLanes(tls)
        self.vi = [i for i, l in enumerate(self.lanes) if not l.startswith(":")]
        self.st = [p.state for p in tl.getAllProgramLogics(tls)[0].phases]
        vs = lambda s: "".join(s[i] for i in self.vi)
        pat = {}
        for k, s in enumerate(self.st):
            v = vs(s)
            if "y" not in v and ("G" in v or "g" in v):
                pat.setdefault(v, []).append(k)
        self.g = []
        for v, ks in pat.items():       # entry = phase with fewest pedestrian greens (none are simulated)
            ent = min(ks, key=lambda k: sum(c in "Gg" for j, c in enumerate(self.st[k]) if j not in self.vi))
            yel = next(j for j in range(max(ks) + 1, max(ks) + len(self.st) + 1) if "y" in vs(self.st[j % len(self.st)])) % len(self.st)
            lanes = {self.lanes[i] for i in self.vi if self.st[ent][i] in "Gg"}
            self.g.append(dict(ent=ent, yel=yel, lanes=sorted(lanes), first=min(ks)))
        self.g.sort(key=lambda d: d["first"])
        self.cur, self.start, self.target = 0, 0, None

    def demand(self, g):
        return sum(traci.lane.getLastStepHaltingNumber(l) + traci.lane.getWaitingTime(l) / 10 for l in self.g[g]["lanes"])

    def wait(self, g):
        return max([traci.vehicle.getWaitingTime(v) for l in self.g[g]["lanes"] for v in traci.lane.getLastStepVehicleIDs(l)] or [0])

    def enter(self, g, now):
        traci.trafficlight.setPhase(self.tls, self.g[g]["ent"]); traci.trafficlight.setPhaseDuration(self.tls, 2)
        self.cur, self.start = g, now

    def switch(self, g):
        traci.trafficlight.setPhase(self.tls, self.g[self.cur]["yel"]); traci.trafficlight.setPhaseDuration(self.tls, YELLOW)
        self.target = g

    def step(self, now):
        if self.target is not None:      # in yellow: jump to the chosen green in the last second of the yellow
            if traci.trafficlight.getNextSwitch(self.tls) - now <= 1:
                self.enter(self.target, now); self.target = None
            return
        if now - self.start < self.p["min_g"]:
            return traci.trafficlight.setPhaseDuration(self.tls, 2)
        demand = {g: self.demand(g) for g in range(len(self.g))}
        wait = {g: self.wait(g) for g in range(len(self.g)) if g != self.cur and demand[g] > 0}
        nxt = choose(self.cur, now - self.start, demand, wait, **self.p)
        if nxt is None:
            traci.trafficlight.setPhaseDuration(self.tls, 2)
        else:
            self.switch(nxt)
