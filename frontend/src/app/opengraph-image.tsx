import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const alt = "HEZQARA — A governed AI workforce for healthcare front-office operations";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

function BrandMark({ dimension, reversed = false }: { dimension: number; reversed?: boolean }) {
  const stroke = reversed ? "#FFFFFF" : "#0F2A47";
  const teal = reversed ? "#2DD4BF" : "#14B8A6";
  const bar = dimension * 0.0917;
  const dot = dimension * 0.15;
  const common = { position: "absolute" as const, backgroundColor: stroke, borderRadius: bar };
  const node = { position: "absolute" as const, width: dot, height: dot, borderRadius: dot, backgroundColor: teal };
  return (
    <div style={{ position: "relative", width: dimension, height: dimension, display: "flex" }}>
      <div style={{ ...common, left: dimension * 0.137, top: dimension * 0.083, width: bar, height: dimension * 0.834 }} />
      <div style={{ ...common, left: dimension * 0.771, top: dimension * 0.083, width: bar, height: dimension * 0.834 }} />
      <div style={{ ...common, left: dimension * 0.137, top: dimension * 0.454, width: dimension * 0.726, height: bar }} />
      <div style={{ ...common, left: dimension * 0.454, top: dimension * 0.183, width: bar, height: dimension * 0.634 }} />
      <div style={{ ...node, left: dimension * 0.425, top: dimension * 0.108 }} />
      <div style={{ ...node, left: dimension * 0.425, top: dimension * 0.742 }} />
      <div style={{ ...node, left: dimension * 0.062, top: dimension * 0.425 }} />
      <div style={{ ...node, left: dimension * 0.696, top: dimension * 0.425 }} />
    </div>
  );
}

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", backgroundColor: "#F4F8FB", padding: 72 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", width: "100%", padding: "68px 64px", borderRadius: 28, border: "1px solid #E4EBF1", backgroundColor: "#FFFFFF" }}>
          <BrandMark dimension={184} />
        </div>
        <div style={{ display: "flex", marginTop: 42, fontSize: 28, lineHeight: 1.4, fontWeight: 500, textAlign: "center", color: "#5B6B7F" }}>
          A governed AI workforce for healthcare front-office operations.
        </div>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 14, backgroundColor: "#0F2A47" }} />
      </div>
    ),
    { ...size },
  );
}
