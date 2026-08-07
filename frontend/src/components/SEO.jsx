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
  }, [title, description, keywords, canonical, ogImage, ogType, noindex]);

  return null;
};

export default SEO;
