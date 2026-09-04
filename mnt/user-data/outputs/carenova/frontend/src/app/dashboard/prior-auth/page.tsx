"use client";
import { useState } from "react";
const T={bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)"};
const DEMO=[
  {id:"PA1",patient:"Maria Santos",medication:"Humira 40mg",carrier:"BlueCross",status:"approved",submitted:"08:30",resolved:"09:12",days:0},
  {id:"PA2",patient:"James Mitchell",medication:"Ozempic 1mg",carrier:"Aetna",status:"pending",submitted:"07:45",resolved:"—",days:1},
  {id:"PA3",patient:"Priya Sharma",medication:"Dupixent 300mg",carrier:"United",status:"more_info",submitted:"Yesterday",resolved:"—",days:2},
  {id:"PA4",patient:"Robert Chen",medication:"Farxiga 10mg",carrier:"Medicare",status:"approved",submitted:"Yesterday",resolved:"Yesterday",days:0},
  {id:"PA5",patient:"Angela White",medication:"Keytruda 200mg",carrier:"Cigna",status:"denied",submitted:"2 days ago",resolved:"Yesterday",days:0},
];
const SC={approved:{color:T.green,bg:"rgba(52,211,153,0.12)"},pending:{color:T.amber,bg:"rgba(245,166,35,0.12)"},more_info:{color:T.purple,bg:"rgba(167,139,250,0.12)"},denied:{color:T.red,bg:"rgba(255,77,106,0.12)"}};
export default function PriorAuthPage() {
  return (
    <div style={{minHeight:"100vh",padding:24,background:T.bg,display:"flex",flexDirection:"column",gap:18}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:900,color:T.white}}>Prior Auth</h1>
          <p style={{fontSize:13,color:T.dim3,marginTop:2}}>Automated prior authorization via FHIR Da Vinci PAS</p>
        </div>
        <div style={{display:"flex",gap:14}}>
          {[{l:"Approved",v:2,c:T.green},{l:"Pending",v:1,c:T.amber},{l:"Needs info",v:1,c:T.purple},{l:"Denied",v:1,c:T.red}].map(s=>(
            <div key={s.l} style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:12,padding:"10px 16px",textAlign:"center"}}>
              <p style={{fontSize:9,color:T.dim3,textTransform:"uppercase",letterSpacing:"0.08em"}}>{s.l}</p>
              <p style={{fontSize:22,fontWeight:900,color:s.c,letterSpacing:"-0.04em"}}>{s.v}</p>
            </div>
          ))}
        </div>
      </div>
      {/* Time saved banner */}
      <div style={{background:T.surface,border:`1px solid ${T.tealBorder}`,borderRadius:16,padding:20,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div>
          <p style={{fontSize:11,color:T.teal,fontWeight:700,textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:4}}>Time saved by automation</p>
          <p style={{fontSize:28,fontWeight:900,color:T.white,letterSpacing:"-0.04em"}}>3h 45m</p>
          <p style={{fontSize:12,color:T.dim3}}>vs. 45min manual per submission</p>
        </div>
        <p style={{fontSize:13,color:T.dim3,maxWidth:260,lineHeight:1.6}}>Prior auth submitted via FHIR Da Vinci PAS — no phone calls, no faxing, automatic status polling every 2 hours.</p>
      </div>
      <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:18,overflow:"hidden"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead>
            <tr style={{borderBottom:`1px solid ${T.border}`}}>
              {["Patient","Medication","Carrier","Status","Submitted","Resolved"].map(h=>(
                <th key={h} style={{textAlign:"left",padding:"12px 20px",fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DEMO.map((pa,i)=>{
              const sc=SC[pa.status as keyof typeof SC]??SC.pending;
              return(
                <tr key={pa.id} style={{borderBottom:i<DEMO.length-1?`1px solid ${T.border}`:"none"}}>
                  <td style={{padding:"12px 20px",fontSize:13,fontWeight:600,color:T.dim1}}>{pa.patient}</td>
                  <td style={{padding:"12px 20px",fontSize:13,color:T.dim2}}>{pa.medication}</td>
                  <td style={{padding:"12px 20px",fontSize:13,color:T.dim2}}>{pa.carrier}</td>
                  <td style={{padding:"12px 20px"}}>
                    <span style={{fontSize:11,fontWeight:600,padding:"3px 10px",borderRadius:100,background:sc.bg,color:sc.color,textTransform:"capitalize"}}>{pa.status.replace("_"," ")}</span>
                  </td>
                  <td style={{padding:"12px 20px",fontSize:12,color:T.dim3}}>{pa.submitted}</td>
                  <td style={{padding:"12px 20px",fontSize:12,color:pa.resolved==="—"?T.dim3:T.green}}>{pa.resolved}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
