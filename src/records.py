"""Batting and career record models."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class BattingLine:
    G:int=0; PA:int=0; AB:int=0; H:int=0; doubles:int=0; triples:int=0; HR:int=0; BB:int=0; SO:int=0; HBP:int=0; SB:int=0; CS:int=0; R:int=0; RBI:int=0
    @property
    def singles(self)->int: return max(0,self.H-self.doubles-self.triples-self.HR)
    @property
    def AVG(self)->float: return self.H/self.AB if self.AB else 0.0
    @property
    def OBP(self)->float: return (self.H+self.BB+self.HBP)/self.PA if self.PA else 0.0
    @property
    def SLG(self)->float:
        return (self.singles+2*self.doubles+3*self.triples+4*self.HR)/self.AB if self.AB else 0.0
    @property
    def OPS(self)->float: return self.OBP+self.SLG
    def record_pa(self,result:str,runs:int=0,rbi:int=0)->None:
        self.PA+=1; self.R+=max(0,runs); self.RBI+=max(0,rbi)
        if result=='walk': self.BB+=1; return
        if result=='hit_by_pitch': self.HBP+=1; return
        self.AB+=1
        if result=='strikeout': self.SO+=1
        elif result=='single': self.H+=1
        elif result=='double': self.H+=1; self.doubles+=1
        elif result=='triple': self.H+=1; self.triples+=1
        elif result=='home_run': self.H+=1; self.HR+=1
        elif result!='out': raise ValueError(f'unsupported plate appearance result: {result}')
    def add(self,other:'BattingLine')->None:
        for name in ('G','PA','AB','H','doubles','triples','HR','BB','SO','HBP','SB','CS','R','RBI'): setattr(self,name,getattr(self,name)+getattr(other,name))
    def as_dict(self)->dict[str,int]:
        return {'G':self.G,'PA':self.PA,'AB':self.AB,'H':self.H,'2B':self.doubles,'3B':self.triples,'HR':self.HR,'BB':self.BB,'SO':self.SO,'HBP':self.HBP,'SB':self.SB,'CS':self.CS,'R':self.R,'RBI':self.RBI}
    @classmethod
    def from_dict(cls,data:dict[str,int])->'BattingLine':
        return cls(G=int(data.get('G',0)),PA=int(data.get('PA',0)),AB=int(data.get('AB',0)),H=int(data.get('H',0)),doubles=int(data.get('2B',data.get('doubles',0))),triples=int(data.get('3B',data.get('triples',0))),HR=int(data.get('HR',0)),BB=int(data.get('BB',0)),SO=int(data.get('SO',0)),HBP=int(data.get('HBP',0)),SB=int(data.get('SB',0)),CS=int(data.get('CS',0)),R=int(data.get('R',0)),RBI=int(data.get('RBI',0)))

@dataclass
class SeasonRecord:
    year:int; age:int; team:str; first_team:BattingLine=field(default_factory=BattingLine); farm:BattingLine=field(default_factory=BattingLine); awards:list[str]=field(default_factory=list)
    def as_dict(self)->dict[str,object]: return {'year':self.year,'age':self.age,'team':self.team,'first_team':self.first_team.as_dict(),'farm':self.farm.as_dict(),'awards':list(self.awards)}
    @classmethod
    def from_dict(cls,data:dict[str,object])->'SeasonRecord':
        return cls(year=int(data['year']),age=int(data['age']),team=str(data['team']),first_team=BattingLine.from_dict(dict(data.get('first_team',{}))),farm=BattingLine.from_dict(dict(data.get('farm',{}))),awards=[str(v) for v in data.get('awards',[])])
