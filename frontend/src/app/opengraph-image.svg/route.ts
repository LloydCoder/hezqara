const image = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630" role="img" aria-labelledby="title desc"><title id="title">HEZQARA — The governed AI workforce for healthcare</title><desc id="desc">A governed AI workforce for healthcare front-office operations.</desc><rect width="1200" height="630" fill="#F4F8FB"/><rect x="100" y="90" width="1000" height="450" rx="28" fill="#FFFFFF" stroke="#E4EBF1" stroke-width="2"/><g transform="translate(540 155) scale(1.1)"><path d="M22 10V110M98 10V110M22 60H98M60 22V98" fill="none" stroke="#0F2A47" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/><circle cx="60" cy="22" r="9" fill="#14B8A6"/><circle cx="60" cy="98" r="9" fill="#14B8A6"/><circle cx="22" cy="60" r="9" fill="#14B8A6"/><circle cx="98" cy="60" r="9" fill="#14B8A6"/></g><text x="600" y="365" text-anchor="middle" fill="#0F2A47" font-family="Inter,Arial,sans-serif" font-size="64" font-weight="800" letter-spacing="8">HEZQARA</text><text x="600" y="430" text-anchor="middle" fill="#5B6B7F" font-family="Inter,Arial,sans-serif" font-size="28">The governed AI workforce for healthcare</text><text x="600" y="475" text-anchor="middle" fill="#0F766E" font-family="Inter,Arial,sans-serif" font-size="21">Healthcare front-office operations</text></svg>`;

export async function GET() {
  return new Response(image, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
