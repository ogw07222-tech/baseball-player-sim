"""H3.1 validation metric accumulator."""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from . import parameters as P


@dataclass
class H3Line:
    pa: int = 0
    ab: int = 0
    h: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    hr: int = 0
    bb: int = 0
    hbp: int = 0
    so: int = 0
    roe: int = 0
    outs: int = 0
    bip: int = 0
    swings: int = 0
    chases: int = 0
    swing_pitch_quality_sum: float = 0.0
    contact_quality_sum: float = 0.0
    contact_quality_count: int = 0
    directions: Counter = field(default_factory=Counter)
    types: Counter = field(default_factory=Counter)
    depths: Counter = field(default_factory=Counter)
    quality_tiers: Counter = field(default_factory=Counter)
    quality_attempts: Counter = field(default_factory=Counter)
    quality_catches: Counter = field(default_factory=Counter)
    difficulty_attempts: Counter = field(default_factory=Counter)
    difficulty_catches: Counter = field(default_factory=Counter)
    difficulty_misses: Counter = field(default_factory=Counter)
    errors_by_difficulty: Counter = field(default_factory=Counter)
    hits_on_miss_by_difficulty: Counter = field(default_factory=Counter)
    infield_hits_by_difficulty: Counter = field(default_factory=Counter)
    double_candidates: int = 0
    stretch_double_candidates: int = 0
    double_downgrades: int = 0
    triple_conversions: int = 0
    single_to_double_upgrades: int = 0
    damage_3b_to_2b: int = 0
    damage_2b_to_1b: int = 0
    raw_trip_candidates: int = 0
    raw_double_candidates: int = 0

    @property
    def avg(self) -> float:
        return self.h / self.ab if self.ab else 0.0

    @property
    def obp(self) -> float:
        return (self.h + self.bb + self.hbp) / self.pa if self.pa else 0.0

    @property
    def slg(self) -> float:
        return (self.singles + 2*self.doubles + 3*self.triples + 4*self.hr) / self.ab if self.ab else 0.0

    @property
    def ops(self) -> float:
        return self.obp + self.slg

    @property
    def babip(self) -> float:
        den = self.ab - self.so - self.hr
        return (self.h - self.hr) / den if den > 0 else 0.0

    @property
    def offensive_value(self) -> float:
        if not self.pa:
            return 0.0
        w = P.OFFENSIVE_WEIGHTS
        return (w["BB"]*self.bb + w["HBP"]*self.hbp + w["1B"]*self.singles +
                w["2B"]*self.doubles + w["3B"]*self.triples + w["HR"]*self.hr +
                w["ROE"]*self.roe) / self.pa

    def as_metrics(self) -> dict[str, float]:
        pa = max(1, self.pa)
        xbh = self.doubles + self.triples + self.hr
        return {
            "PA": self.pa,
            "AVG": self.avg,
            "OBP": self.obp,
            "SLG": self.slg,
            "OPS": self.ops,
            "BABIP": self.babip,
            "HR%": self.hr/pa,
            "BB%": self.bb/pa,
            "K%": self.so/pa,
            "H%": self.h/pa,
            "1B%": self.singles/pa,
            "2B%": self.doubles/pa,
            "3B%": self.triples/pa,
            "XBH%": xbh/pa,
            "BIP%": self.bip/pa,
            "OUT%": self.outs/pa,
            "ERROR%": self.roe/pa,
            "ROE%": self.roe/pa,
            "chase%": self.chases/max(1,self.swings),
            "avg_swing_pitch_quality": self.swing_pitch_quality_sum/max(1,self.swings),
            "avg_contact_quality": self.contact_quality_sum/max(1,self.contact_quality_count),
            "2B_to_1B_downgrade%": self.double_downgrades/max(1,self.stretch_double_candidates),
            "3B_conversion%": self.triple_conversions/max(1,self.double_candidates),
            "1B_to_2B_upgrade%": self.single_to_double_upgrades/max(1,self.singles+self.single_to_double_upgrades),
            "3B_share_2B3B": self.triples/max(1,self.doubles+self.triples),
            "offensive_value": self.offensive_value,
        }
