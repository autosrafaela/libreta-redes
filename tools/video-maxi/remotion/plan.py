import json
sil={int(k):v for k,v in json.load(open("sil.json")).items()}
sil[7]["e"]=3.54; sil[7]["gaps"]=[]; sil[9]["e"]=1.76; sil[9]["gaps"]=[]
TXT={1:["Hay autos que rejuvenecen."],2:["Sí, como tu vecina."],3:["Usa más filtros que moto de wachiturro."],
4:["Soy vendedor de autos hace 15 años y sé","muy puntualmente que hay muchos vehículos que se les bajan los kilómetros."],
5:["El cuentakilómetros se puede bajar.","Libreta no."],
6:["Cada trabajo lo carga el taller, y los kilómetros de ese día, y los kilómetros van únicamente hacia adelante."],
7:["No se puede bajar ni borrar un trabajo."],8:["Si vas a comprar, pedí el historial."],9:["Y si vas a vender, tenelo."],
10:["Ah, ¡es gratis!"],11:["Entrá gratis a libretaapp.com, el link en mi perfil. Saludos."]}
pieces=[]; words=[]; t=0
for i in range(1,12):
    s=sil[i]; a=max(0,s["s"]-0.06); b=min(s["dur"],s["e"]+0.1)
    bounds=[a]+[x for g in s["gaps"] for x in (g[0]+0.06,g[1]-0.06)]+[b]
    clip_start=t
    for k in range(0,len(bounds),2):
        ps,pe=bounds[k],bounds[k+1]
        pieces.append({"clip":i,"s":round(ps,3),"e":round(pe,3),"o":round(t,3)})
        text=TXT[i][k//2]; ws=text.split()
        # speech approx: from piece start+0.06 to end-0.1
        sp0=t+(0.06 if ps==a else 0.06); sp1=t+(pe-ps)-0.1
        wt=[len(w)+2 for w in ws]; tot=sum(wt); acc=0
        for w,x in zip(ws,wt):
            words.append({"w":w,"s":round(sp0+acc/tot*(sp1-sp0),3),"e":round(sp0+(acc+x)/tot*(sp1-sp0),3),"clip":i}); acc+=x
        t+=pe-ps
    print(i,round(clip_start,2),round(t,2))
json.dump({"pieces":pieces,"words":words,"total":round(t,3)},open("plan.json","w"),ensure_ascii=False,indent=0)
print("total",t)
