"""FlowSense rule-based adaptive signal controller (the "brain").

Used by simulation/run_flowsense.py. Rules:
  - minimum green MIN_G seconds, maximum green MAX_G seconds, yellow always kept
  - switch early when the served road empties and another road has cars waiting
  - switch when another road's demand is at least 2x the current one + 3
  - any vehicle waiting more than STARVE seconds forces its phase next
Demand of a phase = stopped vehicles on its lanes + (waiting time / 10).
"""
import traci

MIN_G, MAX_G, YELLOW, STARVE = 8, 60, 3, 90

class Flow:
    def __init__(self, tls):
        tl = traci.trafficlight; self.tls = tls
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
            lanes = {self.lanes[i] for i in self.vi if vs(self.st[ent]) and self.st[ent][i] in "Gg"}
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
        if self.target is not None:
            if traci.trafficlight.getNextSwitch(self.tls) - now <= 1:
                self.enter(self.target, now); self.target = None
            return
        if now - self.start < MIN_G:
            return traci.trafficlight.setPhaseDuration(self.tls, 2)
        oth = [g for g in range(len(self.g)) if g != self.cur]
        dc = self.demand(self.cur); sc = {g: self.demand(g) for g in oth}
        best = max(oth, key=lambda g: sc[g]); db = sc[best]
        starved = [(self.wait(g), g) for g in oth if sc[g] > 0]
        starved = [x for x in starved if x[0] > STARVE]
        if starved: self.switch(max(starved)[1])
        elif now - self.start >= MAX_G and db > 0: self.switch(best)
        elif dc == 0 and db > 0: self.switch(best)
        elif db >= 2 * dc + 3: self.switch(best)
        else: traci.trafficlight.setPhaseDuration(self.tls, 2)
