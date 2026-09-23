import { getCollection } from "astro:content";
import siteDataJson from "./site-data.json";

export const siteData = siteDataJson;

export function siteImage(path?: string, fallback = true) {
  if (!path) return fallback ? siteData.logoPath || siteData.defaultOgImage || "" : "";
  if (path.startsWith("http") || path.startsWith("/")) return path;
  return `/${path}`;
}

export function absoluteUrl(path = "/") {
  const origin = siteData.siteOrigin.replace(/\/$/, "");
  return `${origin}${path.startsWith("/") ? path : `/${path}`}`;
}

export function excerpt(text = "", limit = 120) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  return cleaned.length > limit ? `${cleaned.slice(0, limit)}...` : cleaned;
}

export function schemaDateTime(text?: string) {
  if (!text) return undefined;
  return text.replace(/\./g, "-").replace(" ", "T");
}

export async function getEvents() {
  const items = await getCollection("events");
  return items.sort((a, b) => b.data.sort - a.data.sort);
}

export async function getNotes() {
  const items = await getCollection("notes");
  return items.sort((a, b) => (b.data.sort || 0) - (a.data.sort || 0));
}

export async function getExternalTimeline() {
  const items = await getCollection("external");
  return items.sort((a, b) => b.data.sort - a.data.sort);
}

export async function getSlides() {
  const items = await getCollection("slides");
  return items.sort((a, b) => a.data.sort - b.data.sort);
}

export async function getPage(slug: string) {
  const pages = await getCollection("pages");
  return pages.find((page) => page.id === `${slug}.md`);
}

export async function getReports() {
  const reports = await getCollection("reports");
  return reports.sort((a, b) => a.data.title.localeCompare(b.data.title, "ja"));
}

export async function getReport(slug: string) {
  const reports = await getCollection("reports");
  return reports.find((report) => report.id === `${slug}.md`);
}

export function groupByYear<T extends { date?: string } | { data: { date?: string } }>(items: T[]) {
  return items.reduce<Record<string, T[]>>((groups, item) => {
    const date = "data" in item ? item.data.date : item.date;
    const year = date?.slice(0, 4) || "不明";
    groups[year] ||= [];
    groups[year].push(item);
    return groups;
  }, {});
}

export function themeText(themes: string[]) {
  return themes.length ? themes.join(" / ") : "その他";
}
