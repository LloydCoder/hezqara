"use client";
const T={bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)"};
const DEMO=[
  {id:"REF1",patient:"Maria Santos",from:"Dr. Chen — Family Medicine",to:"Dr. Park — Cardiology",reason:"Chest pain evaluation",status:"scheduled",date:"Jun 28"},
  {id:"REF2",patient:"James Mitchell",from:"Dr. Kim — Internal Med",to:"Dr. Okafor — Endocrinology",reason:"Diabetes management",status:"accepted",date:"Jun 29"},
  {id:"REF3",patient:"Priya Sharma",from:"Dr. Chen — Family Medicine",to:"Dr. Walsh — Dermatology",reason:"Skin lesion evaluation",status:"sent",date:"Jun 29"},
  {id:"REF4",patient:"Robert Chen",from:"Dr. Kim — Internal Med",to:"Dr. Rivera — Gastroenterology",reason:"Colonoscopy prep",status:"initiated",date:"Jun 30"},
];
const SC={scheduled:{c:T.green,bg:"rgba(52,211,153,0.12)"},accepted:{c:T.teal,bg:T.tealDim},sent:{c:T.purple,bg:"rgba(167,139,250,0.12)"},initiated:{c:T.amber,bg:"rgba(245,166,35,0.12)"},completed:{c:"rgba(255,255,255,0.3)",bg:"rgba(255,255,255,0.06)"}};
export default function ReferralsPage() {
  return (
    <div style={{minHeight:"100vh",padding:24,background:T.bg,display:"flex",flexDirection:"column",gap:18}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:900,color:T.white}}>Referrals</h1>
          <p style={{fontSize:13,color:T.dim3,marginTop:2}}>Specialist referrals — created and tracked end-to-end</p>
        </div>
        <button style={{background:T.tealDim,border:`1px solid ${T.tealBorder}`,borderRadius:12,padding:"9px 18px",color:T.teal,fontSize:13,fontWeight:600,cursor:"pointer"}}>+ New Referral</button>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14}}>
        {[{l:"Active referrals",v:4,c:T.teal},{l:"Scheduled",v:1,c:T.green},{l:"Accepted",v:1,c:T.purple},{l:"Avg days to appt",v:"3.2",c:T.amber}].map(s=>(
          <div key={s.l} style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:14,padding:18}}>
            <p style={{fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3}}>{s.l}</p>
            <p style={{fontSize:28,fontWeight:900,color:s.c,marginTop:6,letterSpacing:"-0.04em"}}>{s.v}</p>
          </div>
        ))}
      </div>
      <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:18,overflow:"hidden"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead>
            <tr style={{borderBottom:`1px solid ${T.border}`}}>
              {["Patient","From","To Specialist","Reason","Status","Date"].map(h=>(
                <th key={h} style={{textAlign:"left",padding:"12px 20px",fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DEMO.map((r,i)=>{
              const sc=SC[r.status as keyof typeof SC]??SC.initiated;
              return(
                <tr key={r.id} style={{borderBottom:i<DEMO.length-1?`1px solid ${T.border}`:"none"}}>
                  <td style={{padding:"12px 20px",fontSize:13,fontWeight:600,color:T.dim1}}>{r.patient}</td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim2}}>{r.from}</td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim2}}>{r.to}</td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim2}}>{r.reason}</td>
                  <td style={{padding:"12px 20px"}}><span style={{fontSize:11,fontWeight:600,padding:"3px 10px",borderRadius:100,background:sc.bg,color:sc.c,textTransform:"capitalize"}}>{r.status}</span></td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim3}}>{r.date}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
