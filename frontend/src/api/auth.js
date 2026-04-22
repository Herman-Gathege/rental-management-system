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