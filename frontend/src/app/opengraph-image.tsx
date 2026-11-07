import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "HEZQARA — The governed AI workforce for healthcare";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", width: "100%", height: "100%", padding: 80, backgroundColor: "#F4F8FB", color: "#0F2A47", fontFamily: "Arial" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", padding: "76px 40px", borderRadius: 24, backgroundColor: "#FFFFFF", border: "2px solid #E4EBF1" }}>
          <div style={{ display: "flex", fontSize: 76, fontWeight: 800, letterSpacing: 8 }}>HEZQARA</div>
        </div>
        <div style={{ display: "flex", marginTop: 44, fontSize: 28, lineHeight: 1.4, fontWeight: 500, textAlign: "center", color: "#5B6B7F" }}>
          The governed AI workforce for healthcare
        </div>
        <div style={{ display: "flex", marginTop: 18, fontSize: 20, color: "#0F766E" }}>Healthcare front-office operations</div>
      </div>
    ),
    { ...size },
  );
}
