//frontend\src\api\expenseCategories.js

import API from "./client";

export const getExpenseCategories = async (includeInactive = false) => {
  const params = includeInactive ? { include_inactive: true } : {};
  const { data } = await API.get("/expense-categories/", { params });
  return data;
};

export const createExpenseCategory = async (payload) => {
  const { data } = await API.post("/expense-categories/", payload);
  return data;
};

export const updateExpenseCategory = async (id, payload) => {
  const { data } = await API.put(`/expense-categories/${id}`, payload);
  return data;
};
