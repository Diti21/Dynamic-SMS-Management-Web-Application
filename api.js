import axios from "axios";

// Set up the base URL for the backend API
const api = axios.create({
  baseURL: "http://localhost:8000",
});

// Add an interceptor to attach the token to each request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
