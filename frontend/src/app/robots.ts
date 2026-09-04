import type { MetadataRoute } from "next";
export default function robots():MetadataRoute.Robots{const base=process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/,"")??"http://localhost:3004";return{rules:{userAgent:"*",allow:"/",disallow:["/dashboard/","/api/"]},sitemap:`${base}/sitemap.xml`};}
