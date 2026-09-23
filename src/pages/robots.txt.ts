import { siteData } from "../lib/archive";

export function GET() {
  return new Response(`User-agent: *\nAllow: /\nSitemap: ${siteData.siteOrigin.replace(/\/$/, "")}/sitemap.xml\n`, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}

