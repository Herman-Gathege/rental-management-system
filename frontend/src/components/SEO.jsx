import { useEffect } from "react";
import { updateSEO, DEFAULT_SEO } from "../utils/seo";

const SEO = ({
  title,
  description,
  keywords,
  canonical,
  ogImage,
  ogType,
  noindex = false,
  jsonLd,
}) => {
  useEffect(() => {
    updateSEO({
      title: title || DEFAULT_SEO.title,
      description: description || DEFAULT_SEO.description,
      keywords: keywords || DEFAULT_SEO.keywords,
      canonical: canonical || DEFAULT_SEO.canonical,
      ogImage: ogImage || DEFAULT_SEO.ogImage,
      ogType,
    });

    if (noindex) {
      let robots = document.querySelector('meta[name="robots"]');
      if (!robots) {
        robots = document.createElement("meta");
        robots.name = "robots";
        document.head.appendChild(robots);
      }
      robots.setAttribute("content", "noindex, nofollow");
    } else {
      let robots = document.querySelector('meta[name="robots"]');
      if (robots) {
        robots.setAttribute("content", "index, follow");
      }
    }

    if (jsonLd) {
      let script = document.querySelector('script[type="application/ld+json"][data-seo-jsonld]');
      if (!script) {
        script = document.createElement("script");
        script.setAttribute("type", "application/ld+json");
        script.setAttribute("data-seo-jsonld", "true");
        document.head.appendChild(script);
      }
      script.textContent = JSON.stringify(jsonLd);
    }
  }, [title, description, keywords, canonical, ogImage, ogType, noindex, jsonLd]);

  return null;
};

export default SEO;
