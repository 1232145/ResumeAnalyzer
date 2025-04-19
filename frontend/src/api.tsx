import axios from 'axios';

const api = axios.create({
  baseURL: 'http://ec2-51-20-34-225.eu-north-1.compute.amazonaws.com:5000/',
  // baseURL: 'http://127.0.0.1:5000',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data
      });
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;
