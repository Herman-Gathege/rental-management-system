//frontend/src/api/auth.js
import API from "./client";

/* LOGIN */
export const loginUser = async (email, password) => {
  const { data } = await API.post("/auth/login", {
    email,
    password,
  });
  return data;
};

/* REGISTER LANDLORD */
export const registerUser = async (payload) => {
  const { data } = await API.post("/auth/register", payload);
  return data;
};

/* GET CURRENT USER */
export const getMe = async () => {
  const { data } = await API.get("/auth/me");
  return data;
};

/* UPDATE PROFILE (currently just full_name) — returns the updated /me payload */
export const updateProfile = async (payload) => {
  const { data } = await API.put("/auth/me", payload);
  return data;
};

/* CHANGE PASSWORD — payload: { current_password, new_password } */
export const changePassword = async (payload) => {
  const { data } = await API.post("/auth/change-password", payload);
  return data;
};

/* ─── Phone verification OTP (Sprint 6.2 #6) ─── */

/* Verify the 6-digit WhatsApp code for the signed-in user. */
export const verifyOtp = async (code) => {
  const { data } = await API.post("/auth/verify-otp", { code });
  return data;
};

/* Resend the OTP (60s throttle server-side). Optionally correct the phone. */
export const resendOtp = async (phone = null) => {
  const { data } = await API.post("/auth/resend-otp", phone ? { phone } : {});
  return data;
};
