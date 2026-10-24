from __future__ import annotations
from dataclasses import dataclass
PRIORITY_ORDER={"Crítica":0,"Muy alta":1,"Alta":2,"Media":3,"Baja":4,"Normal":5,"Pendiente de criticidad":6,"Revisar":7}
PRIORITY_SCORE={"Crítica":100,"Muy alta":90,"Alta":75,"Media":55,"Baja":35,"Normal":15,"Pendiente de criticidad":0,"Revisar":0}
@dataclass(frozen=True)
class OperationalPrioritySummary:
    critical:int; very_high:int; high:int; medium:int; low:int; normal:int; pending:int
def _clean(v): return " ".join(str(v or "").split()).strip()
def _num(v,d=0.0):
    try: return float(str(v).replace(",","."))
    except: return d
def classify_operational_priority(stock_priority,criticality):
    stock_priority=_clean(stock_priority); criticality=_clean(criticality)
    if criticality not in {"Alta","Media","Baja"}: return "Pendiente de criticidad"
    m={"Alta":{"Urgente":"Crítica","Alta":"Muy alta","Media":"Alta","Normal":"Normal","Revisar":"Revisar"},"Media":{"Urgente":"Muy alta","Alta":"Alta","Media":"Media","Normal":"Normal","Revisar":"Revisar"},"Baja":{"Urgente":"Alta","Alta":"Media","Media":"Baja","Normal":"Normal","Revisar":"Revisar"}}
    return m[criticality].get(stock_priority,"Revisar")
def explain_priority(stock_priority,criticality,coverage,state):
    if _clean(criticality) not in {"Alta","Media","Baja"}: return "Pendiente: falta definir criticidad operativa institucional."
    return f"Criticidad {_clean(criticality)}; prioridad de stock {_clean(stock_priority)}; cobertura {_num(coverage):.1f}%; estado {_clean(state)}."
class OperationalPriorityMatrix:
    def __init__(self,rows): self.rows=[dict(r) for r in rows]
    def enrich_rows(self):
        out=[]
        for row in self.rows:
            r=dict(row); crit=_clean(r.get("Criticidad")); sp=_clean(r.get("Prioridad stock") or r.get("Prioridad")); op=classify_operational_priority(sp,crit)
            r["Prioridad operativa"]=op; r["Puntaje prioridad"]=PRIORITY_SCORE.get(op,0); r["Justificación prioridad"]=explain_priority(sp,crit,r.get("Cobertura stock %"),r.get("Estado reposición")); out.append(r)
        return sorted(out,key=lambda r:(PRIORITY_ORDER.get(r.get("Prioridad operativa"),99),-_num(r.get("Reposición sugerida")),-_num(r.get("Cantidad")),str(r.get("Descripción",""))))
    def summary(self):
        c={k:0 for k in ["Crítica","Muy alta","Alta","Media","Baja","Normal","Pendiente de criticidad"]}
        for r in self.enrich_rows():
            k=r.get("Prioridad operativa"); c[k]=c.get(k,0)+1
        return OperationalPrioritySummary(c["Crítica"],c["Muy alta"],c["Alta"],c["Media"],c["Baja"],c["Normal"],c["Pendiente de criticidad"])
    def actionable_rows(self,include_pending=False):
        a={"Crítica","Muy alta","Alta","Media","Baja"}
        if include_pending: a.add("Pendiente de criticidad")
        return [r for r in self.enrich_rows() if r.get("Prioridad operativa") in a]
