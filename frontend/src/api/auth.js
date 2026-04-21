import API from "./client";

/* LOGIN */
export const loginUser = async (email, password) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const res = await API.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  return res.data;
};

/* REGISTER */
export const registerUser = async (data) => {
  const res = await API.post("/auth/register", data);
  return res.data;
};

/* GET CURRENT USER */
export const getMe = async () => {
  const res = await API.get("/auth/me");
  return res.data;
};