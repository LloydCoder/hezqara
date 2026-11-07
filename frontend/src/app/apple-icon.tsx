import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  const dimension = 128;
  const bar = dimension * 0.0917;
  const dot = dimension * 0.15;
  const stroke = "#FFFFFF";
  const teal = "#2DD4BF";
  const common = { position: "absolute" as const, backgroundColor: stroke, borderRadius: bar };
  const node = { position: "absolute" as const, width: dot, height: dot, borderRadius: dot, backgroundColor: teal };
  return new ImageResponse(
    <div style={{ width: 180, height: 180, display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "#0B1220", borderRadius: 36 }}>
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
    </div>,
    size,
  );
}
