//frontend\src\api\organizations.js

import API from "./client";

/* GET current user's organization */
export const getMyOrganization = async () => {
  const { data } = await API.get("/organizations/me");
  return data;
};

/* INVITE a user to the organization */
export const inviteUser = async (email, role) => {
  const { data } = await API.post("/organizations/invite", { email, role });
  return data;
};

/* ACCEPT an invitation by token */
export const acceptInvitation = async (token) => {
  const { data } = await API.post(`/organizations/accept-invite/${token}`);
  return data;
};

/* LIST pending invitations */
export const getInvitations = async () => {
  const { data } = await API.get("/organizations/invitations");
  return data;
};