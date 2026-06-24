//frontend\src\api\notifications.js
import API from "./client";

export const getNotifications = async (unreadOnly = false) => {
  const params = unreadOnly ? { unread_only: true } : {};
  const { data } = await API.get("/notifications/", { params });
  return data;
};

export const markNotificationRead = async (id) => {
  const { data } = await API.put(`/notifications/${id}/read`);
  return data;
};

export const markAllNotificationsRead = async () => {
  const { data } = await API.put("/notifications/read-all");
  return data;
};
