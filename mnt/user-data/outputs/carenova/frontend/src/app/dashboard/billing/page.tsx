"use client";
const T={bg:"#0B1120",surface:"#0F1729",border:"rgba(255,255,255,0.07)",teal:"#00E5CC",tealDim:"rgba(0,229,204,0.12)",tealBorder:"rgba(0,229,204,0.2)",amber:"#F5A623",green:"#34D399",purple:"#A78BFA",red:"#FF4D6A",white:"#FFFFFF",dim1:"rgba(255,255,255,0.75)",dim2:"rgba(255,255,255,0.45)",dim3:"rgba(255,255,255,0.2)",dim4:"rgba(255,255,255,0.06)"};
const PLANS=[
  {id:"starter",label:"Starter",price:499,priceNGN:25000,providers:"1–2",color:T.teal},
  {id:"pro",label:"Pro",price:999,priceNGN:49000,providers:"3–5",color:T.purple,current:true},
  {id:"growth",label:"Growth",price:1999,priceNGN:99000,providers:"6–15",color:T.amber},
  {id:"enterprise",label:"Enterprise",price:3999,priceNGN:199000,providers:"15+",color:T.green},
];
const FEATURES={starter:["All 10 AI agents","athenahealth integration","HIPAA compliant","Email + SMS reminders","Dashboard analytics"],pro:["Everything in Starter","Prior auth automation","Insurance verification","Recall campaigns","Operations Copilot","Priority support"],growth:["Everything in Pro","Multi-location","Epic SMART on FHIR","Advanced analytics","Dedicated onboarding"],enterprise:["Everything in Growth","ACH bank transfer","NET-30 invoicing","Custom EHR integration","SLA guarantee","White-glove onboarding"]};
export default function BillingPage() {
  const current="pro";
  return (
    <div style={{minHeight:"100vh",padding:24,background:T.bg,display:"flex",flexDirection:"column",gap:18}}>
      <div>
        <h1 style={{fontSize:20,fontWeight:900,color:T.white}}>Billing</h1>
        <p style={{fontSize:13,color:T.dim3,marginTop:2}}>Subscription and payment management</p>
      </div>
      {/* Current plan banner */}
      <div style={{background:T.surface,border:`1px solid ${T.tealBorder}`,borderRadius:18,padding:24,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div>
          <p style={{fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3,marginBottom:6}}>Current plan</p>
          <p style={{fontSize:28,fontWeight:900,color:T.purple,letterSpacing:"-0.04em"}}>Pro — $999/month</p>
          <p style={{fontSize:12,color:T.dim3,marginTop:4}}>3–5 providers · Renews July 1, 2026 · LemonSqueezy</p>
        </div>
        <div style={{textAlign:"right"}}>
          <p style={{fontSize:12,color:T.dim3,marginBottom:8}}>Next invoice</p>
          <p style={{fontSize:24,fontWeight:900,color:T.white,letterSpacing:"-0.04em"}}>$999.00</p>
          <button style={{marginTop:10,background:T.dim4,border:`1px solid ${T.border}`,borderRadius:10,padding:"8px 16px",color:T.dim2,fontSize:12,cursor:"pointer"}}>Manage subscription →</button>
        </div>
      </div>
      {/* Plans grid */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14}}>
        {PLANS.map(p=>{
          const feats=FEATURES[p.id as keyof typeof FEATURES]??[];
          const isCurrent=p.id===current;
          return(
            <div key={p.id} style={{background:T.surface,border:`1px solid ${isCurrent?p.color+"50":T.border}`,borderRadius:18,padding:20,position:"relative"}}>
              {isCurrent&&<div style={{position:"absolute",top:-11,left:"50%",transform:"translateX(-50%)",background:p.color,borderRadius:100,padding:"2px 12px",fontSize:10,fontWeight:700,color:"#070C17",whiteSpace:"nowrap"}}>CURRENT</div>}
              <p style={{fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3,marginBottom:8}}>{p.label}</p>
              <p style={{fontSize:32,fontWeight:900,letterSpacing:"-0.04em",color:p.color,lineHeight:1}}>${p.price}<span style={{fontSize:14,fontWeight:500,color:T.dim3}}>/mo</span></p>
              <p style={{fontSize:11,color:T.dim3,marginTop:4,marginBottom:16}}>{p.providers} providers</p>
              <div style={{display:"flex",flexDirection:"column",gap:6,marginBottom:20}}>
                {feats.map(f=>(
                  <div key={f} style={{display:"flex",alignItems:"center",gap:8}}>
                    <span style={{color:p.color,fontSize:11,flexShrink:0}}>✓</span>
                    <span style={{fontSize:12,color:T.dim2}}>{f}</span>
                  </div>
                ))}
              </div>
              <button style={{width:"100%",padding:"10px",borderRadius:12,fontSize:13,fontWeight:600,cursor:isCurrent?"default":"pointer",border:"none",background:isCurrent?p.color+"18":T.dim4,color:isCurrent?p.color:T.dim3,border:`1px solid ${isCurrent?p.color+"30":T.border}`}}>
                {isCurrent?"Current plan":"Upgrade"}
              </button>
            </div>
          );
        })}
      </div>
      {/* Nigeria pricing note */}
      <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:16,padding:20}}>
        <p style={{fontSize:13,fontWeight:700,color:T.dim1,marginBottom:12}}>Nigeria pricing (via Paystack)</p>
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14}}>
          {PLANS.map(p=>(
            <div key={p.id}>
              <p style={{fontSize:11,color:T.dim3,marginBottom:4}}>{p.label}</p>
              <p style={{fontSize:18,fontWeight:800,color:p.color,letterSpacing:"-0.03em"}}>₦{p.priceNGN.toLocaleString()}</p>
              <p style={{fontSize:10,color:T.dim3}}>per month</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
