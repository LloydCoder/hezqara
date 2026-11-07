import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const runtime = "nodejs";

export async function GET() {
  const logoSource = await readFile(
    join(process.cwd(), "public/brand/hezqara-logo-horizontal-tagline-full-color.svg"),
    "utf8",
  );
  const logoMarkup = logoSource
    .replace(/^<svg\\b[^>]*>/, "")
    .replace(/<\\/svg>\\s*$/, "");

  const image = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630" role="img" aria-labelledby="title desc"><title id="title">HEZQARA — The governed AI workforce for healthcare</title><desc id="desc">A governed AI workforce for healthcare front-office operations.</desc><rect width="1200" height="630" fill="#F4F8FB"/><rect x="100" y="90" width="1000" height="450" rx="28" fill="#FFFFFF" stroke="#E4EBF1" stroke-width="2"/><svg x="350" y="190" width="500" height="134" viewBox="0 0 357.54 96.00">${logoMarkup}</svg><text x="600" y="410" text-anchor="middle" fill="#0F2A47" font-family="Inter,Arial,sans-serif" font-size="28" font-weight="600">A governed AI workforce for healthcare</text><text x="600" y="458" text-anchor="middle" fill="#0F766E" font-family="Inter,Arial,sans-serif" font-size="21">Healthcare front-office operations</text></svg>`;

  return new Response(image, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
