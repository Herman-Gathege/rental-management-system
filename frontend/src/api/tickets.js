//frontend\src\api\tickets.js
import API from "./client";

// ─── Tickets CRUD ───

export const getTickets = async (filters = {}) => {
  const { data } = await API.get("/tickets/", { params: filters });
  return data;
};

export const getTicket = async (id) => {
  const { data } = await API.get(`/tickets/${id}`);
  return data;
};

export const createTicket = async (payload) => {
  const { data } = await API.post("/tickets/", payload);
  return data;
};

export const updateTicket = async (id, payload) => {
  const { data } = await API.put(`/tickets/${id}`, payload);
  return data;
};

export const deleteTicket = async (id) => {
  const { data } = await API.delete(`/tickets/${id}`);
  return data;
};

// ─── Lifecycle transitions ───

export const assignTicket = async (id, payload) => {
  const { data } = await API.post(`/tickets/${id}/assign`, payload);
  return data;
};

export const startTicket = async (id, note = null) => {
  const { data } = await API.post(`/tickets/${id}/start`, { reason: note });
  return data;
};

export const waitTicket = async (id, note = null) => {
  const { data } = await API.post(`/tickets/${id}/wait`, { reason: note });
  return data;
};

export const resolveTicket = async (id, note = null) => {
  const { data } = await API.post(`/tickets/${id}/resolve`, { reason: note });
  return data;
};

export const closeTicket = async (id, note = null) => {
  const { data } = await API.post(`/tickets/${id}/close`, { reason: note });
  return data;
};

export const reopenTicket = async (id, note = null) => {
  const { data } = await API.post(`/tickets/${id}/reopen`, { reason: note });
  return data;
};

// ─── Messages ───

export const getMessages = async (ticketId) => {
  const { data } = await API.get(`/tickets/${ticketId}/messages`);
  return data;
};

export const addMessage = async (ticketId, payload) => {
  const { data } = await API.post(`/tickets/${ticketId}/messages`, payload);
  return data;
};

export const deleteMessage = async (ticketId, messageId) => {
  const { data } = await API.delete(`/tickets/${ticketId}/messages/${messageId}`);
  return data;
};

// ─── Attachments ───

export const getAttachments = async (ticketId) => {
  const { data } = await API.get(`/tickets/${ticketId}/attachments`);
  return data;
};

export const uploadAttachment = async (ticketId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await API.post(`/tickets/${ticketId}/attachments`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const deleteAttachment = async (ticketId, attachmentId) => {
  const { data } = await API.delete(
    `/tickets/${ticketId}/attachments/${attachmentId}`
  );
  return data;
};
