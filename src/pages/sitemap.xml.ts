import { getCollection } from "astro:content";
import { siteData } from "../lib/archive";

export async function GET() {
  const events = await getCollection("events");
  const reports = await getCollection("reports");
  const paths = [
    "/",
    "/timeline.html",
    "/themes.html",
    "/analysis.html",
    "/about.html",
    "/research.html",
    ...reports.map((report) => `/reports/${report.id.replace(/\.md$/, "")}.html`),
    ...events.filter((event) => event.data.hasDetail).map((event) => `/${event.data.page}`),
  ];
  const origin = siteData.siteOrigin.replace(/\/$/, "");
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${paths.map((path) => `  <url><loc>${origin}${path}</loc></url>`).join("\n")}\n</urlset>\n`, {
    headers: { "Content-Type": "application/xml" },
  });
}
