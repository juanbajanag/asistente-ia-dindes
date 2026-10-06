"""Utilidades modulares para el diagnóstico de overfitting/underfitting del proyecto DINDES.

El módulo implementa preparación de datos, tracking de métricas, balanceo, feature engineering
y evaluación. No realiza fine-tuning del LLM Qwen; trabaja sobre un clasificador auxiliar de
relevancia pregunta-documento.
"""
from __future__ import annotations
import copy, re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import log_loss, accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.utils.class_weight import compute_class_weight


def generar_variantes(texto: str, n_variantes: int = 5) -> list[str]:
    reemplazos=[('¿',''),('?',''),(' de ',' del '),('Qué ','Que '),('sistema','solución')]
    variantes=[]
    for i in range(n_variantes):
        a,b=reemplazos[i % len(reemplazos)]
        variantes.append(str(texto).replace(a,b,1))
    return variantes


def construir_pares(answerable: pd.DataFrame, docs: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for _,q in answerable.iterrows():
        expected=str(q['expected_source_id']).split(';')[0]
        for _,d in docs.iterrows():
            text=f"pregunta: {q['question']} documento: {d['title']} {d['section']} {d['text']}"
            rows.append([q['qa_id'],text,int(str(d['document_id'])==expected)])
    return pd.DataFrame(rows,columns=['qa_id','pair_text','label'])


def split_por_qa_id(pairs: pd.DataFrame, seed: int = 42, n_val: int = 2):
    qa_ids=np.array(sorted(pairs.qa_id.unique()))
    qa_ids=np.random.default_rng(seed).permutation(qa_ids)
    val_ids=set(qa_ids[:n_val]); train_ids=set(qa_ids[n_val:])
    train=pairs[pairs.qa_id.isin(train_ids)].reset_index(drop=True)
    val=pairs[pairs.qa_id.isin(val_ids)].reset_index(drop=True)
    assert set(train.qa_id).isdisjoint(set(val.qa_id))
    return train,val,train_ids,val_ids


def aumentar_solo_training(train_original: pd.DataFrame, n_variantes: int = 5) -> pd.DataFrame:
    rows=[]
    for _,row in train_original.iterrows():
        rows.append(row.to_dict())
        for v in generar_variantes(row.pair_text,n_variantes):
            rows.append({'qa_id':row.qa_id,'pair_text':v,'label':row.label})
    return pd.DataFrame(rows)


def entrenar_sgd_tracking(X_train,y_train,X_val,y_val,alpha=1e-7,epochs=50,balanced=False,seed=42):
    model=SGDClassifier(loss='log_loss',penalty='l2',alpha=alpha,random_state=seed)
    classes=np.array([0,1]); rng=np.random.default_rng(seed); y_arr=np.asarray(y_train)
    sample_weights=np.ones(len(y_arr),dtype=float)
    if balanced:
        weights=compute_class_weight(class_weight='balanced',classes=classes,y=y_arr)
        wd=dict(zip(classes,weights)); sample_weights=np.array([wd[v] for v in y_arr])
    history=[]; snapshots=[]
    for epoch in range(1,epochs+1):
        idx=rng.permutation(X_train.shape[0])
        model.partial_fit(X_train[idx],y_arr[idx],classes=classes,sample_weight=sample_weights[idx])
        p_tr=model.predict_proba(X_train); p_va=model.predict_proba(X_val)
        yh_tr=model.predict(X_train); yh_va=model.predict(X_val)
        history.append({'epoch':epoch,
            'train_loss':log_loss(y_train,p_tr,labels=[0,1]),
            'val_loss':log_loss(y_val,p_va,labels=[0,1]),
            'train_acc':accuracy_score(y_train,yh_tr),
            'val_acc':accuracy_score(y_val,yh_va),
            'val_precision':precision_score(y_val,yh_va,zero_division=0),
            'val_recall':recall_score(y_val,yh_va,zero_division=0),
            'val_f1':f1_score(y_val,yh_va,zero_division=0)})
        snapshots.append(copy.deepcopy(model))
    return model,pd.DataFrame(history),snapshots


def tokenizar(texto: str) -> set[str]:
    return set(re.findall(r"\b[a-záéíóúñ0-9\-\.]+\b",str(texto).lower()))


def overlap_ratio(q: str,d: str) -> float:
    tq=tokenizar(q); td=tokenizar(d)
    return len(tq & td)/len(tq) if tq else 0.0


def length_ratio(q: str,d: str) -> float:
    lq=len(str(q)); ld=len(str(d))
    return min(lq,ld)/max(lq,ld) if max(lq,ld)>0 else 0.0


def technical_overlap(q: str,d: str) -> float:
    tq=tokenizar(q); td=tokenizar(d)
    tech={t for t in tq if any(c.isdigit() for c in t) or '-' in t}
    return len(tech & td)/len(tech) if tech else 0.0


def crear_features(df: pd.DataFrame, tfidf: TfidfVectorizer) -> pd.DataFrame:
    features=[]
    for _,r in df.iterrows():
        v=tfidf.transform([r.question,r.document_text])
        features.append({
            'cosine_similarity':cosine_similarity(v[0],v[1])[0,0],
            'overlap_ratio':overlap_ratio(r.question,r.document_text),
            'length_ratio':length_ratio(r.question,r.document_text),
            'technical_overlap':technical_overlap(r.question,r.document_text)})
    return pd.DataFrame(features)


def metricas_clasificacion(y_true,y_pred) -> dict[str,float]:
    return {
        'accuracy':accuracy_score(y_true,y_pred),
        'precision':precision_score(y_true,y_pred,zero_division=0),
        'recall':recall_score(y_true,y_pred,zero_division=0),
        'f1':f1_score(y_true,y_pred,zero_division=0)}
