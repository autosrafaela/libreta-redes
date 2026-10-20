import soundfile as sf, numpy as np, json
res={}
for i in range(1,12):
    a,sr=sf.read(f"a{i:02d}.wav",dtype='float32'); hop=int(0.02*sr)
    db=np.array([20*np.log10(np.sqrt((a[k:k+hop]**2).mean()+1e-12)) for k in range(0,len(a)-hop,hop)])
    thr=max(db.max()-30, np.percentile(db,15)+5)
    v=np.where(db>thr)[0]; s=v[0]*0.02; e=(v[-1]+1)*0.02
    # internal gaps
    low=db<thr; gaps=[]; k=v[0]
    while k<v[-1]:
        if low[k]:
            j=k
            while low[j]: j+=1
            if (j-k)*0.02>=0.3: gaps.append((round(k*0.02,2),round(j*0.02,2)))
            k=j
        else: k+=1
    res[i]={"dur":round(len(a)/sr,2),"s":round(s,2),"e":round(e,2),"gaps":gaps}
    print(i,res[i])
json.dump(res,open("sil.json","w"))
