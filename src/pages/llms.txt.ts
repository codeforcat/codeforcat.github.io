import { siteData } from "../lib/archive";

export function GET() {
  return new Response(`# ${siteData.siteName}\n\nテクノロジーによりネコとヒトの素敵な関係をつくる、Code for CATの公式サイトです。\n\n主要ページ:\n- /archive.html\n- /timeline.html\n- /themes.html\n- /analysis.html\n- /about.html\n- /research.html\n`, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
