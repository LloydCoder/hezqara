import { useState, useEffect } from "react";

const T = {
  bg:"#0B1120", surface:"#0F1729", surfaceHi:"#141E35",
  border:"rgba(255,255,255,0.07)", borderHi:"rgba(255,255,255,0.14)",
  teal:"#00E5CC", tealDim:"rgba(0,229,204,0.12)", tealBorder:"rgba(0,229,204,0.2)",
  amber:"#F5A623", amberDim:"rgba(245,166,35,0.12)",
  red:"#FF4D6A", redDim:"rgba(255,77,106,0.12)",
  green:"#34D399", greenDim:"rgba(52,211,153,0.12)",
  purple:"#A78BFA",
  white:"#FFFFFF",
  dim1:"rgba(255,255,255,0.78)", dim2:"rgba(255,255,255,0.48)",
  dim3:"rgba(255,255,255,0.22)", dim4:"rgba(255,255,255,0.07)",
};

const S = (x={}) => ({fontFamily:"-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",boxSizing:"border-box",...x});

// ── Sample queue data ─────────────────────────────────────────────────────────
const INITIAL_QUEUE = [
  {id:"V001",num:1,name:"Amaka Obi",         complaint:"Fever and headache",    wait:6,  status:"waiting",  priority:"normal",  lang:"ig"},
  {id:"V002",num:2,name:"Chukwu Nwosu",      complaint:"Chest pain",            wait:18, status:"waiting",  priority:"emergency",lang:"ig"},
  {id:"V003",num:3,name:"Ngozi Adeyemi",     complaint:"Antenatal checkup",     wait:30, status:"waiting",  priority:"normal",  lang:"yo"},
  {id:"V004",num:4,name:"Emmanuel Okeke",    complaint:"Malaria symptoms",      wait:42, status:"waiting",  priority:"normal",  lang:"ig"},
  {id:"V005",num:5,name:"Blessing Eze",      complaint:"Follow-up visit",       wait:54, status:"waiting",  priority:"normal",  lang:"en"},
  {id:"V006",num:6,name:"Chidinma Okonkwo",  complaint:"Baby vaccination",      wait:66, status:"waiting",  priority:"normal",  lang:"ig"},
  {id:"V007",num:7,name:"Sunday Nwoye",      complaint:"Hypertension checkup",  wait:78, status:"waiting",  priority:"normal",  lang:"en"},
];

const LANG_FLAGS = {
  en:"🇬🇧", ig:"🟢", yo:"🟡", ha:"🔵", fr:"🇫🇷",
  sw:"🇰🇪", hi:"🇮🇳", fil:"🇵🇭", ar:"🇦🇪",
};

function PingDot({color=T.teal, size=8}) {
  return (
    <span style={S({position:"relative",display:"inline-flex",width:size,height:size})}>
      <span style={S({position:"absolute",inset:0,borderRadius:"50%",background:color,
        opacity:0.7,animation:"ping 1.4s cubic-bezier(0,0,0.2,1) infinite"})}/>
      <span style={S({position:"relative",width:size,height:size,borderRadius:"50%",background:color})}/>
    </span>
  );
}

function StatBox({label,value,sub,color}) {
  return (
    <div style={S({background:T.surface,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px 18px"})}>
      <p style={S({fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.dim3,marginBottom:6})}>{label}</p>
      <p style={S({fontSize:28,fontWeight:900,letterSpacing:"-0.04em",color,lineHeight:1})}>{value}</p>
      {sub&&<p style={S({fontSize:11,color:T.dim3,marginTop:4})}>{sub}</p>}
    </div>
  );
}

// ── QR Code display ───────────────────────────────────────────────────────────
function QRDisplay({clinicName, phone}) {
  const waUrl = `https://wa.me/${phone.replace(/\D/g,"")}?text=Hi+I+am+here+to+check+in`;

  return (
    <div style={S({background:T.surface,border:`1px solid ${T.border}`,borderRadius:18,padding:24,textAlign:"center"})}>
      <p style={S({fontSize:13,fontWeight:700,color:T.dim1,marginBottom:4})}>Walk-In QR Code</p>
      <p style={S({fontSize:11,color:T.dim3,marginBottom:16})}>Print and place at reception</p>

      {/* QR code representation */}
      <div style={S({
        width:160,height:160,margin:"0 auto 16px",
        background:T.white,borderRadius:12,padding:12,
        display:"flex",alignItems:"center",justifyContent:"center",
        flexDirection:"column",gap:4,
      })}>
        {/* Fake QR pattern */}
        <div style={S({display:"grid",gridTemplateColumns:"repeat(7,1fr)",gap:2,width:120})}>
          {Array.from({length:49}).map((_,i)=>{
            const corners = [0,1,2,3,4,5,6,7,13,14,20,21,27,28,34,35,41,42,43,44,45,46,47,48];
            const isCorner = corners.includes(i);
            const isFilled = isCorner || Math.random() > 0.5;
            return (
              <div key={i} style={S({
                width:"100%",paddingBottom:"100%",
                background:isFilled?"#0B1120":"transparent",
                borderRadius:1,
              })}/>
            );
          })}
        </div>
        <div style={S({width:32,height:32,borderRadius:8,
          background:"linear-gradient(135deg,#00E5CC,#0099BB)",
          display:"flex",alignItems:"center",justifyContent:"center",
          fontSize:14,fontWeight:900,color:"#070C17",marginTop:4})}>C</div>
      </div>

      <p style={S({fontSize:11,color:T.dim3,marginBottom:8})}>
        Patient scans → WhatsApp opens → checks in
      </p>

      <div style={S({background:T.tealDim,border:`1px solid ${T.tealBorder}`,
        borderRadius:10,padding:"8px 12px",marginTop:8})}>
        <p style={S({fontSize:10,color:T.teal,fontWeight:600,marginBottom:2})}>Works in 8 languages</p>
        <p style={S({fontSize:10,color:T.dim3})}>🇬🇧 🟢 🟡 🔵 🇫🇷 🇰🇪 🇮🇳 🇵🇭</p>
      </div>
    </div>
  );
}

// ── Walk-in simulation ────────────────────────────────────────────────────────
function WalkInSimulator({onCheckin}) {
  const [name,setName]=useState("");
  const [complaint,setComplaint]=useState("");
  const [lang,setLang]=useState("en");
  const [showSim,setShowSim]=useState(false);
  const [simMsg,setSimMsg]=useState("");

  const DEMO_PATIENTS = [
    {name:"Kemi Okafor",   complaint:"Stomach pain",      lang:"yo"},
    {name:"Ahmed Musa",    complaint:"Cough and cold",    lang:"ha"},
    {name:"Marie Koné",    complaint:"Consultation",      lang:"fr"},
    {name:"Priya Sharma",  complaint:"Fever",             lang:"hi"},
    {name:"Juan Santos",   complaint:"Check-up",          lang:"fil"},
  ];

  const simulateCheckin = () => {
    const demo = DEMO_PATIENTS[Math.floor(Math.random()*DEMO_PATIENTS.length)];
    setSimMsg(`${LANG_FLAGS[demo.lang] || "🌍"} *${demo.name}* just checked in via WhatsApp → "${demo.complaint}"`);
    onCheckin({name:demo.name,complaint:demo.complaint,lang:demo.lang});
    setTimeout(()=>setSimMsg(""),4000);
  };

  const manualCheckin = () => {
    if(!name||!complaint) return;
    onCheckin({name,complaint,lang});
    setName(""); setComplaint("");
    setShowSim(false);
  };

  return (
    <div style={S({background:T.surface,border:`1px solid ${T.border}`,borderRadius:18,padding:20})}>
      <div style={S({display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:14})}>
        <p style={S({fontSize:13,fontWeight:700,color:T.dim1})}>Walk-In Simulator</p>
        <button onClick={()=>setShowSim(!showSim)}
          style={S({background:T.dim4,border:`1px solid ${T.border}`,borderRadius:8,
            padding:"5px 12px",fontSize:11,color:T.dim3,cursor:"pointer"})}>
          {showSim?"Hide":"Manual"}
        </button>
      </div>

      {simMsg&&(
        <div style={S({background:T.greenDim,border:`1px solid ${T.green}30`,
          borderRadius:10,padding:"10px 12px",marginBottom:12,
          fontSize:12,color:T.green})}>
          ✓ {simMsg}
        </div>
      )}

      {showSim&&(
        <div style={S({display:"flex",flexDirection:"column",gap:8,marginBottom:12})}>
          <input value={name} onChange={e=>setName(e.target.value)}
            placeholder="Patient full name"
            style={S({padding:"9px 12px",borderRadius:9,background:T.dim4,
              border:`1px solid ${T.border}`,color:T.dim1,fontSize:12,outline:"none"})}/>
          <input value={complaint} onChange={e=>setComplaint(e.target.value)}
            placeholder="Chief complaint"
            style={S({padding:"9px 12px",borderRadius:9,background:T.dim4,
              border:`1px solid ${T.border}`,color:T.dim1,fontSize:12,outline:"none"})}/>
          <select value={lang} onChange={e=>setLang(e.target.value)}
            style={S({padding:"9px 12px",borderRadius:9,background:T.surface,
              border:`1px solid ${T.border}`,color:T.dim1,fontSize:12,outline:"none"})}>
            {[["en","English"],["ig","Igbo"],["yo","Yoruba"],["ha","Hausa"],
              ["fr","French"],["sw","Swahili"],["hi","Hindi"],["fil","Filipino"]].map(([v,l])=>(
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
          <button onClick={manualCheckin}
            style={S({padding:"9px",borderRadius:9,background:T.tealDim,
              border:`1px solid ${T.tealBorder}`,color:T.teal,fontSize:12,
              fontWeight:600,cursor:"pointer"})}>
            Add to Queue
          </button>
        </div>
      )}

      <button onClick={simulateCheckin}
        style={S({width:"100%",padding:"11px",borderRadius:11,
          background:"linear-gradient(135deg,#00E5CC,#0099BB)",
          border:"none",color:"#070C17",fontSize:13,fontWeight:700,cursor:"pointer"})}>
        📱 Simulate WhatsApp Walk-In
      </button>

      <p style={S({fontSize:10,color:T.dim3,textAlign:"center",marginTop:8})}>
        Simulates a patient scanning the QR code and checking in
      </p>
    </div>
  );
}

// ── Queue card ────────────────────────────────────────────────────────────────
function QueueCard({entry, onCallNext, isNext}) {
  const isEmergency = entry.priority==="emergency";
  const borderColor = isEmergency ? T.red+"60" : isNext ? T.tealBorder : T.border;
  const bg = isEmergency ? T.redDim : isNext ? T.tealDim : T.dim4;

  return (
    <div style={S({
      background:bg,border:`1px solid ${borderColor}`,
      borderRadius:14,padding:"14px 16px",
      display:"flex",alignItems:"center",gap:12,
      transition:"all 0.2s",
    })}>
      {/* Queue number */}
      <div style={S({
        width:40,height:40,borderRadius:11,flexShrink:0,
        background:isEmergency?T.red:isNext?T.teal:T.surface,
        border:`1px solid ${isEmergency?T.red:isNext?T.teal:T.border}`,
        display:"flex",alignItems:"center",justifyContent:"center",
        fontSize:16,fontWeight:900,
        color:isEmergency||isNext?"#070C17":T.dim3,
      })}>
        {isEmergency?"🚨":entry.num}
      </div>

      {/* Patient info */}
      <div style={S({flex:1,minWidth:0})}>
        <div style={S({display:"flex",alignItems:"center",gap:6,marginBottom:2})}>
          <p style={S({fontSize:13,fontWeight:700,color:T.dim1,
            whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"})}>
            {entry.name}
          </p>
          <span style={S({fontSize:12,flexShrink:0})}>{LANG_FLAGS[entry.lang]||"🌍"}</span>
          {isEmergency&&(
            <span style={S({fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:100,
              background:T.redDim,color:T.red,border:`1px solid ${T.red}30`,flexShrink:0})}>
              EMERGENCY
            </span>
          )}
        </div>
        <p style={S({fontSize:11,color:T.dim3,
          whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"})}>
          {entry.complaint}
        </p>
      </div>

      {/* Wait time */}
      <div style={S({textAlign:"right",flexShrink:0})}>
        <p style={S({fontSize:11,color:isEmergency?T.red:T.dim3,fontWeight:isEmergency?700:400})}>
          {isEmergency?"Priority":entry.wait+"m wait"}
        </p>
        {isNext&&(
          <p style={S({fontSize:10,color:T.teal,fontWeight:600})}>Next up</p>
        )}
      </div>

      {/* Call button */}
      {isNext&&(
        <button onClick={()=>onCallNext(entry)}
          style={S({
            background:"linear-gradient(135deg,#00E5CC,#0099BB)",
            border:"none",borderRadius:9,padding:"8px 14px",
            color:"#070C17",fontSize:12,fontWeight:700,cursor:"pointer",
            flexShrink:0,
          })}>
          Call →
        </button>
      )}
    </div>
  );
}

// ── Called patient card ───────────────────────────────────────────────────────
function CalledCard({entry, onComplete}) {
  return (
    <div style={S({
      background:T.amberDim,border:`1px solid ${T.amber}40`,
      borderRadius:14,padding:"14px 16px",
      display:"flex",alignItems:"center",gap:12,
    })}>
      <div style={S({width:36,height:36,borderRadius:10,flexShrink:0,
        background:T.amber,display:"flex",alignItems:"center",
        justifyContent:"center",fontSize:18,color:"#070C17"})}>⚕</div>
      <div style={S({flex:1,minWidth:0})}>
        <p style={S({fontSize:13,fontWeight:700,color:T.dim1})}>{entry.name}</p>
        <p style={S({fontSize:11,color:T.amber})}>With doctor · {entry.room||"Room 1"}</p>
      </div>
      <div style={S({display:"flex",gap:6,flexShrink:0})}>
        <button onClick={()=>onComplete(entry.id,"7 days")}
          style={S({background:T.greenDim,border:`1px solid ${T.green}30`,
            borderRadius:8,padding:"7px 12px",color:T.green,
            fontSize:11,fontWeight:600,cursor:"pointer"})}>
          ✓ Done
        </button>
        <button onClick={()=>onComplete(entry.id,null)}
          style={S({background:T.dim4,border:`1px solid ${T.border}`,
            borderRadius:8,padding:"7px 12px",color:T.dim3,
            fontSize:11,cursor:"pointer"})}>
          No-show
        </button>
      </div>
    </div>
  );
}

// ── Main walk-in dashboard ────────────────────────────────────────────────────
export default function WalkInDashboard() {
  const [queue, setQueue] = useState(INITIAL_QUEUE);
  const [called, setCalled] = useState([]);
  const [completed, setCompleted] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [totalToday, setTotalToday] = useState(INITIAL_QUEUE.length);

  // Sort queue: emergencies first, then by number
  const sortedQueue = [...queue].sort((a,b)=>{
    if(a.priority==="emergency"&&b.priority!=="emergency") return -1;
    if(b.priority==="emergency"&&a.priority!=="emergency") return 1;
    return a.num-b.num;
  });

  const addNotification = (msg, color=T.teal) => {
    const id = Date.now();
    setNotifications(p=>[{id,msg,color},...p.slice(0,2)]);
    setTimeout(()=>setNotifications(p=>p.filter(n=>n.id!==id)),4000);
  };

  const handleCheckin = ({name, complaint, lang}) => {
    const num = totalToday+1;
    setTotalToday(num);
    const entry = {
      id:`V${num.toString().padStart(3,"0")}`,
      num, name, complaint, lang,
      wait: Math.max(5, queue.length * 12),
      status:"waiting", priority:"normal",
    };
    setQueue(p=>[...p,entry]);
    addNotification(`📱 ${name} checked in via WhatsApp → "${complaint}"`, T.green);
  };

  const handleCallNext = (entry) => {
    setQueue(p=>p.filter(e=>e.id!==entry.id));
    setCalled(p=>[...p,{...entry,room:"Room 1",status:"called"}]);
    addNotification(`🔔 Notifying ${entry.name} to come to Room 1`, T.amber);
  };

  const handleComplete = (id, followUpDays) => {
    const entry = called.find(e=>e.id===id);
    if(!entry) return;
    setCalled(p=>p.filter(e=>e.id!==id));
    setCompleted(p=>[...p,{...entry,status:"completed"}]);
    if(followUpDays) {
      addNotification(`📅 Follow-up reminder scheduled for ${entry.name} in ${followUpDays}`, T.purple);
    } else {
      addNotification(`✓ Visit complete — ${entry.name}`, T.green);
    }
  };

  const estimatedWait = Math.max(5, sortedQueue.length * 12);
  const avgWait = queue.length > 0
    ? Math.round(queue.reduce((s,e)=>s+e.wait,0)/queue.length)
    : 0;

  return (
    <div style={S({minHeight:"100vh",background:T.bg,padding:20})}>
      <style>{`
        @keyframes ping{75%,100%{transform:scale(2);opacity:0}}
        *{box-sizing:border-box;margin:0;padding:0}
      `}</style>

      {/* Header */}
      <div style={S({display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:20})}>
        <div>
          <div style={S({display:"flex",alignItems:"center",gap:10,marginBottom:4})}>
            <div style={S({width:32,height:32,borderRadius:9,
              background:"linear-gradient(135deg,#00E5CC,#0099BB)",
              display:"flex",alignItems:"center",justifyContent:"center",
              fontWeight:900,fontSize:14,color:"#070C17"})}>C</div>
            <h1 style={S({fontSize:18,fontWeight:900,color:T.white,letterSpacing:"-0.02em"})}>
              Walk-In Queue
            </h1>
          </div>
          <p style={S({fontSize:12,color:T.dim3})}>
            Owerri Family Clinic · Live queue management
          </p>
        </div>
        <div style={S({display:"flex",alignItems:"center",gap:8})}>
          <PingDot/>
          <span style={S({fontSize:11,fontWeight:600,color:T.teal})}>Live</span>
        </div>
      </div>

      {/* Notifications */}
      <div style={S({marginBottom:16})}>
        {notifications.map(n=>(
          <div key={n.id} style={S({
            background:n.color+"14",border:`1px solid ${n.color}30`,
            borderRadius:10,padding:"9px 12px",marginBottom:6,
            fontSize:12,color:n.color,
          })}>{n.msg}</div>
        ))}
      </div>

      {/* Stats */}
      <div style={S({display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:20})}>
        <StatBox label="Waiting now"     value={sortedQueue.length} sub="in queue"                color={T.teal}   />
        <StatBox label="With doctor"     value={called.length}      sub="being seen"              color={T.amber}  />
        <StatBox label="Completed today" value={completed.length}   sub="discharged"              color={T.green}  />
        <StatBox label="Est. wait"       value={`${estimatedWait}m`} sub="for next patient"       color={T.purple} />
      </div>

      {/* Main grid */}
      <div style={S({display:"grid",gridTemplateColumns:"1fr 320px",gap:16})}>

        {/* Queue list */}
        <div style={S({display:"flex",flexDirection:"column",gap:12})}>

          {/* Currently with doctor */}
          {called.length > 0 && (
            <div>
              <p style={S({fontSize:11,fontWeight:700,letterSpacing:"0.1em",
                textTransform:"uppercase",color:T.amber,marginBottom:8})}>
                With Doctor
              </p>
              <div style={S({display:"flex",flexDirection:"column",gap:8})}>
                {called.map(e=>(
                  <CalledCard key={e.id} entry={e} onComplete={handleComplete}/>
                ))}
              </div>
            </div>
          )}

          {/* Waiting queue */}
          <div>
            <div style={S({display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:8})}>
              <p style={S({fontSize:11,fontWeight:700,letterSpacing:"0.1em",
                textTransform:"uppercase",color:T.dim3})}>
                Waiting ({sortedQueue.length})
              </p>
              {sortedQueue.length > 0 && called.length === 0 && (
                <button onClick={()=>handleCallNext(sortedQueue[0])}
                  style={S({background:"linear-gradient(135deg,#00E5CC,#0099BB)",
                    border:"none",borderRadius:9,padding:"7px 16px",
                    color:"#070C17",fontSize:12,fontWeight:700,cursor:"pointer"})}>
                  Call Next →
                </button>
              )}
            </div>
            {sortedQueue.length === 0 ? (
              <div style={S({background:T.surface,border:`1px solid ${T.border}`,
                borderRadius:14,padding:"32px 20px",textAlign:"center"})}>
                <p style={S({fontSize:36,marginBottom:10})}>✅</p>
                <p style={S({fontSize:14,fontWeight:700,color:T.dim2,marginBottom:4})}>Queue is empty</p>
                <p style={S({fontSize:11,color:T.dim3})}>All patients have been seen</p>
              </div>
            ) : (
              <div style={S({display:"flex",flexDirection:"column",gap:8})}>
                {sortedQueue.map((entry,i)=>(
                  <QueueCard key={entry.id} entry={entry}
                    onCallNext={handleCallNext}
                    isNext={i===0&&called.length===0}/>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right panel */}
        <div style={S({display:"flex",flexDirection:"column",gap:12})}>
          <QRDisplay clinicName="Owerri Family Clinic" phone="+2348031000001"/>
          <WalkInSimulator onCheckin={handleCheckin}/>

          {/* Language stats */}
          <div style={S({background:T.surface,border:`1px solid ${T.border}`,
            borderRadius:14,padding:16})}>
            <p style={S({fontSize:12,fontWeight:700,color:T.dim1,marginBottom:12})}>
              Patient Languages Today
            </p>
            {Object.entries(
              [...queue,...called,...completed].reduce((acc,e)=>{
                acc[e.lang]=(acc[e.lang]||0)+1; return acc;
              },{})
            ).map(([lang,count])=>(
              <div key={lang} style={S({display:"flex",alignItems:"center",
                gap:8,marginBottom:6})}>
                <span style={S({fontSize:14})}>{LANG_FLAGS[lang]||"🌍"}</span>
                <span style={S({fontSize:12,color:T.dim2,flex:1})}>
                  {{"en":"English","ig":"Igbo","yo":"Yoruba","ha":"Hausa",
                    "fr":"French","sw":"Swahili","hi":"Hindi","fil":"Filipino"}[lang]||lang}
                </span>
                <span style={S({fontSize:12,fontWeight:700,color:T.teal})}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
