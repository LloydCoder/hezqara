"use client";
const T={bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)"};
const DEMO=[
  {id:"RR1",patient:"Maria Santos",type:"Complete Medical Records",requested:"Jun 28, 09:14",status:"verified",released:true,destination:"Patient portal"},
  {id:"RR2",patient:"James Mitchell",type:"Lab Results — CBC",requested:"Jun 28, 08:30",status:"verified",released:true,destination:"Referring physician"},
  {id:"RR3",patient:"Priya Sharma",type:"Imaging — Chest X-ray",requested:"Jun 29, 07:45",status:"pending_auth",released:false,destination:"Insurance"},
  {id:"RR4",patient:"Robert Chen",type:"Discharge Summary",requested:"Jun 27, 15:20",status:"verified",released:true,destination:"Primary care MD"},
];
const SC={verified:{c:T.green,bg:"rgba(52,211,153,0.12)"},pending_auth:{c:T.amber,bg:"rgba(245,166,35,0.12)"},denied:{c:T.red,bg:"rgba(255,77,106,0.12)"}};
export default function RecordsPage() {
  return (
    <div style={{minHeight:"100vh",padding:24,background:T.bg,display:"flex",flexDirection:"column",gap:18}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:900,color:T.white}}>Records</h1>
          <p style={{fontSize:13,color:T.dim3,marginTop:2}}>HIPAA-compliant record release — identity verified by AI</p>
        </div>
      </div>
      <div style={{background:T.surface,border:`1px solid ${T.tealBorder}`,borderRadius:16,padding:20,display:"flex",alignItems:"center",gap:16}}>
        <span style={{fontSize:22,color:T.teal}}>◈</span>
        <div>
          <p style={{fontSize:13,fontWeight:600,color:T.teal}}>Identity verified before every release</p>
          <p style={{fontSize:12,color:T.dim2}}>Records Agent verifies caller identity via DOB + last 4 of SSN before releasing any PHI. Every release audit-logged.</p>
        </div>
      </div>
      <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:18,overflow:"hidden"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead>
            <tr style={{borderBottom:`1px solid ${T.border}`}}>
              {["Patient","Record Type","Requested","Status","Released","Destination"].map(h=>(
                <th key={h} style={{textAlign:"left",padding:"12px 20px",fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DEMO.map((r,i)=>{
              const sc=SC[r.status as keyof typeof SC]??SC.pending_auth;
              return(
                <tr key={r.id} style={{borderBottom:i<DEMO.length-1?`1px solid ${T.border}`:"none"}}>
                  <td style={{padding:"12px 20px",fontSize:13,fontWeight:600,color:T.dim1}}>{r.patient}</td>
                  <td style={{padding:"12px 20px",fontSize:13,color:T.dim2}}>{r.type}</td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim3}}>{r.requested}</td>
                  <td style={{padding:"12px 20px"}}><span style={{fontSize:11,fontWeight:600,padding:"3px 10px",borderRadius:100,background:sc.bg,color:sc.c,textTransform:"capitalize"}}>{r.status.replace("_"," ")}</span></td>
                  <td style={{padding:"12px 20px",fontSize:13,color:r.released?T.green:T.dim3}}>{r.released?"✓ Released":"Pending"}</td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim2}}>{r.destination}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
