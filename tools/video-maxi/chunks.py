import soundfile as sf, numpy as np, sherpa_onnx, json, sys
a,sr=sf.read(sys.argv[1],dtype='float32')
hop=int(0.02*sr); rms=np.array([np.sqrt((a[i:i+hop]**2).mean()+1e-12) for i in range(0,len(a)-hop,hop)])
db=20*np.log10(rms); thr=np.percentile(db,20)+4
print('thr',thr, 'p20',np.percentile(db,20),'p80',np.percentile(db,80))
# gaps: runs below thr
low=db<thr; gaps=[]; i=0
while i<len(low):
    if low[i]:
        j=i
        while j<len(low) and low[j]: j+=1
        if (j-i)*0.02>=0.12: gaps.append((i*0.02,j*0.02))
        i=j
    else: i+=1
print('gaps',[(round(x,2),round(y,2)) for x,y in gaps])
# chunks between gap midpoints, merging to >=1.2s
cuts=[0]+[(x+y)/2 for x,y in gaps]+[len(a)/sr]
segs=[]; s=cuts[0]
for c in cuts[1:]:
    if c-s>=1.2 or c==cuts[-1]: segs.append((s,c)); s=c
d=sys.argv[2]
R=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{d}/small-encoder.int8.onnx", decoder=f"{d}/small-decoder.int8.onnx", tokens=f"{d}/small-tokens.txt", language="es", task="transcribe", num_threads=4)
out=[]
for s,e in segs:
    st=R.create_stream(); st.accept_waveform(sr,a[int(s*sr):int(e*sr)]); R.decode_stream(st)
    out.append({"s":round(s,2),"e":round(e,2),"t":st.result.text.strip()}); print(out[-1])
json.dump({"gaps":gaps,"segs":out},open(sys.argv[3],'w'),ensure_ascii=False,indent=1)
