"use client";
import { useState, useEffect } from "react";
import api from "@/lib/api";
const CLINIC_ID = process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic";
const T={bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)"};
const DEMO=[
  {id:"I1",patient:"Maria Santos",carrier:"BlueCross BlueShield",plan:"PPO Gold",member_id:"BCB-847291",status:"active",copay:25,deductible_remaining:800,verified_at:"09:14"},
  {id:"I2",patient:"James Mitchell",carrier:"Aetna",plan:"HMO Silver",member_id:"AET-123456",status:"active",copay:30,deductible_remaining:1200,verified_at:"09:08"},
  {id:"I3",patient:"Priya Sharma",carrier:"United Healthcare",plan:"PPO Platinum",member_id:"UHC-789012",status:"active",copay:20,deductible_remaining:0,verified_at:"08:55"},
  {id:"I4",patient:"Robert Chen",carrier:"Medicare",plan:"Part B",member_id:"MED-345678",status:"active",copay:0,deductible_remaining:226,verified_at:"08:30"},
  {id:"I5",patient:"Amaka Obi",carrier:"NHIS",plan:"Basic",member_id:"NHIS-001",status:"pending",copay:0,deductible_remaining:0,verified_at:"—"},
];
export default function InsurancePage() {
  return (
    <div style={{minHeight:"100vh",padding:24,background:T.bg,display:"flex",flexDirection:"column",gap:18}}>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:900,color:T.white}}>Insurance</h1>
          <p style={{fontSize:13,color:T.dim3,marginTop:2}}>Eligibility verification and coverage details</p>
        </div>
        <div style={{display:"flex",gap:14}}>
          {[{l:"Verified today",v:"4",c:T.green},{l:"Pending",v:"1",c:T.amber},{l:"Avg copay",v:"$19",c:T.teal}].map(s=>(
            <div key={s.l} style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:12,padding:"10px 18px",textAlign:"center"}}>
              <p style={{fontSize:10,color:T.dim3,textTransform:"uppercase",letterSpacing:"0.08em"}}>{s.l}</p>
              <p style={{fontSize:20,fontWeight:900,color:s.c,letterSpacing:"-0.04em"}}>{s.v}</p>
            </div>
          ))}
        </div>
      </div>
      <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:18,overflow:"hidden"}}>
        <table style={{width:"100%",borderCollapse:"collapse"}}>
          <thead>
            <tr style={{borderBottom:`1px solid ${T.border}`}}>
              {["Patient","Carrier","Plan","Member ID","Copay","Deductible Left","Status","Verified"].map(h=>(
                <th key={h} style={{textAlign:"left",padding:"12px 16px",fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DEMO.map((ins,i)=>(
              <tr key={ins.id} style={{borderBottom:i<DEMO.length-1?`1px solid ${T.border}`:"none"}}>
                <td style={{padding:"12px 16px",fontSize:13,fontWeight:600,color:T.dim1}}>{ins.patient}</td>
                <td style={{padding:"12px 16px",fontSize:13,color:T.dim2}}>{ins.carrier}</td>
                <td style={{padding:"12px 16px",fontSize:13,color:T.dim2}}>{ins.plan}</td>
                <td style={{padding:"12px 16px",fontSize:12,fontFamily:"monospace",color:T.dim3}}>{ins.member_id}</td>
                <td style={{padding:"12px 16px",fontSize:13,fontWeight:700,color:ins.copay===0?T.green:T.amber}}>${ins.copay}</td>
                <td style={{padding:"12px 16px",fontSize:13,color:ins.deductible_remaining===0?T.green:T.dim2}}>${ins.deductible_remaining}</td>
                <td style={{padding:"12px 16px"}}>
                  <span style={{fontSize:11,fontWeight:600,padding:"3px 10px",borderRadius:100,background:ins.status==="active"?"rgba(52,211,153,0.12)":"rgba(245,166,35,0.12)",color:ins.status==="active"?T.green:T.amber}}>{ins.status}</span>
                </td>
                <td style={{padding:"12px 16px",fontSize:12,fontFamily:"monospace",color:T.dim3}}>{ins.verified_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
