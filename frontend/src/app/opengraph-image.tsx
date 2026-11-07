import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const alt = "HEZQARA — The governed AI workforce for healthcare";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", backgroundColor: "#F4F8FB", padding: 72, color: "#0F2A47" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", padding: "64px", borderRadius: 28, border: "1px solid #E4EBF1", backgroundColor: "#FFFFFF" }}>
          <svg width={190} height={190} viewBox="0 0 120 120" role="img" aria-label="HEZQARA connected H mark">
            <path d="M22 10V110M98 10V110M22 60H98M60 22V98" fill="none" stroke="#0F2A47" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="60" cy="22" r="9" fill="#14B8A6" />
            <circle cx="60" cy="98" r="9" fill="#14B8A6" />
            <circle cx="22" cy="60" r="9" fill="#14B8A6" />
            <circle cx="98" cy="60" r="9" fill="#14B8A6" />
          </svg>
        </div>
        <div style={{ display: "flex", marginTop: 30, fontSize: 52, lineHeight: 1, fontWeight: 800, letterSpacing: "0.12em", color: "#0F2A47" }}>HEZQARA</div>
        <div style={{ display: "flex", marginTop: 18, fontSize: 27, lineHeight: 1.4, fontWeight: 500, textAlign: "center", color: "#0F766E" }}>
          The governed AI workforce for healthcare
        </div>
        <div style={{ display: "flex", marginTop: 12, fontSize: 20, lineHeight: 1.4, textAlign: "center", color: "#5B6B7F" }}>
          A governed AI workforce for healthcare front-office operations.
        </div>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 14, backgroundColor: "#0F2A47" }} />
      </div>
    ),
    { ...size },
  );
}
