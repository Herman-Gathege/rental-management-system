//frontend/src/api/client.js
import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

/* Attach access token automatically */
API.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ─── Silent refresh on 401 ─────────────────────────────────────────────
   When the short-lived access token expires, transparently exchange the
   refresh token for a new access token (POST /auth/refresh?token=...), then
   replay the original request. The user never sees a logout.

   - A bare axios instance (no interceptors) does the refresh, so refreshing
     can't recurse back into this handler.
   - Single-flight: if several requests 401 at once, they all wait on one
     refresh call instead of stampeding the endpoint.
   - If refresh itself fails (refresh token expired/invalid), the session is
     cleared and we send the user to /login. */

const refreshClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

let refreshPromise = null;

function clearSessionAndRedirect() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("active_property_id");
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    // Only act on a first-time 401, and never on the refresh call itself.
    if (
      status !== 401 ||
      !original ||
      original._retry ||
      (original.url && original.url.includes("/auth/refresh"))
    ) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      clearSessionAndRedirect();
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      // Share a single in-flight refresh across concurrent 401s.
      if (!refreshPromise) {
        refreshPromise = refreshClient
          .post("/auth/refresh", null, { params: { token: refreshToken } })
          .then((res) => res.data.access_token)
          .finally(() => {
            refreshPromise = null;
          });
      }

      const newAccessToken = await refreshPromise;
      localStorage.setItem("access_token", newAccessToken);

      // Replay the original request; the request interceptor will attach the
      // fresh token automatically.
      return API(original);
    } catch (refreshError) {
      clearSessionAndRedirect();
      return Promise.reject(refreshError);
    }
  }
);

export default API;