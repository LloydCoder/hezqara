import { ImageResponse } from "next/og";

export const size = { width: 512, height: 512 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "#0B1220", borderRadius: 96 }}>
      <svg width={350} height={350} viewBox="0 0 120 120">
        <path d="M22 10V110M98 10V110M22 60H98M60 22V98" fill="none" stroke="#FFFFFF" strokeWidth="11" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="60" cy="22" r="9" fill="#2DD4BF" />
        <circle cx="60" cy="98" r="9" fill="#2DD4BF" />
        <circle cx="22" cy="60" r="9" fill="#2DD4BF" />
        <circle cx="98" cy="60" r="9" fill="#2DD4BF" />
      </svg>
    </div>,
    size,
  );
}
