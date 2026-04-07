/**
 * ProfielScore Rapport Proxy
 * Fetcht rapport HTML uit Supabase Storage en serveert met text/html content-type.
 * Supabase Storage forceert text/plain voor HTML bestanden (XSS preventie),
 * dus deze proxy is nodig om het rapport correct te renderen.
 *
 * Usage: /.netlify/functions/rapport?path=20260407/Wouter_Arts/rapport.html
 */

const SUPABASE_URL = process.env.SUPABASE_URL || "https://jdistoacicmzdazdaubh.supabase.co";
const BUCKET = "profielscore-assets";

exports.handler = async (event) => {
  const path = event.queryStringParameters?.path;

  if (!path) {
    return {
      statusCode: 400,
      body: "Missing ?path= parameter",
    };
  }

  // Sanitize: only allow alphanumeric, slashes, underscores, hyphens, dots
  if (!/^[a-zA-Z0-9/_.\-]+$/.test(path)) {
    return {
      statusCode: 400,
      body: "Invalid path",
    };
  }

  const storageUrl = `${SUPABASE_URL}/storage/v1/object/public/${BUCKET}/${path}`;

  try {
    const response = await fetch(storageUrl);

    if (!response.ok) {
      return {
        statusCode: response.status,
        body: `Rapport niet gevonden (${response.status})`,
      };
    }

    const html = await response.text();

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "public, max-age=86400",
      },
      body: html,
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: `Fout bij ophalen rapport: ${err.message}`,
    };
  }
};
