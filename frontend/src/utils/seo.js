export const SITE_URL = "https://alphaone.africa";
export const SITE_NAME = "AlphaOne";

const KEYWORDS = [
  "rental property management Kenya",
  "property management East Africa",
  "landlord management software Kenya",
  "tenant management Kenya",
  "rent collection Kenya",
  "property management platform Africa",
  "real estate management Kenya",
  "apartment management East Africa",
  "rental management software Africa",
  "property management Nairobi",
  "landlord app Kenya",
  "rent payment Kenya",
  "lease management Kenya",
  "property management system East Africa",
];

export const DEFAULT_SEO = {
  title: `${SITE_NAME} — Rental Property Management Platform for Kenya & East Africa`,
  description:
    "Streamline rent collection, tenant management, and property operations across Kenya and East Africa. The smart rental property management platform built for landlords, property managers, and tenants.",
  keywords: KEYWORDS.join(", "),
  canonical: SITE_URL,
  ogType: "website",
  ogImage: "https://alphaone.africa/assets/aplha1_logo_.png",
};

export const updateSEO = ({
  title,
  description,
  keywords,
  canonical,
  ogImage,
  ogType,
}) => {
  if (typeof document === "undefined") return;

  document.title = title;

  const setMeta = (name, content) => {
    if (!content) return;
    let tag = document.querySelector(`meta[name="${name}"]`);
    if (!tag) {
      tag = document.createElement("meta");
      tag.name = name;
      document.head.appendChild(tag);
    }
    tag.setAttribute("content", content);
  };

  const setProp = (property, content) => {
    if (!content) return;
    let tag = document.querySelector(`meta[property="${property}"]`);
    if (!tag) {
      tag = document.createElement("meta");
      tag.setAttribute("property", property);
      document.head.appendChild(tag);
    }
    tag.setAttribute("content", content);
  };

  setMeta("description", description);
  setMeta("keywords", keywords);
  setMeta("author", SITE_NAME);

  setProp("og:title", title);
  setProp("og:description", description);
  setProp("og:type", ogType || "website");
  setProp("og:url", canonical);
  if (ogImage) {
    setProp("og:image", ogImage);
  }

  setMeta("twitter:card", "summary_large_image");
  setMeta("twitter:title", title);
  setMeta("twitter:description", description);
  if (ogImage) {
    setMeta("twitter:image", ogImage);
  }

  let canonicalTag = document.querySelector('link[rel="canonical"]');
  if (!canonicalTag) {
    canonicalTag = document.createElement("link");
    canonicalTag.rel = "canonical";
    document.head.appendChild(canonicalTag);
  }
  canonicalTag.setAttribute("href", canonical);
};
