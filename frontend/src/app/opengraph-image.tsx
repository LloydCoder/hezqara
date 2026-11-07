import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const alt = "HEZQARA — The governed AI workforce for healthcare";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpenGraphImage() {
  const logoBytes = await readFile(join(process.cwd(), "public", "brand", "hezqara-logo-horizontal-tagline-full-color.svg"));
  const logoSrc = `data:image/svg+xml;base64,${logoBytes.toString("base64")}`;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#F4F8FB",
          padding: 72,
          color: "#0F2A47",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            padding: "72px 64px",
            borderRadius: 28,
            border: "1px solid #E4EBF1",
            backgroundColor: "#FFFFFF",
          }}
        >
          <img src={logoSrc} width="680" height="183" />
        </div>
        <div style={{ marginTop: 42, fontSize: 28, lineHeight: 1.4, fontWeight: 500, textAlign: "center" }}>
          A governed AI workforce for healthcare front-office operations.
        </div>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 14, backgroundColor: "#0F2A47" }} />
      </div>
    ),
    { ...size },
  );
}
