import axios from 'axios';

const api = axios.create({
  baseURL: 'http://ec2-51-20-34-225.eu-north-1.compute.amazonaws.com:5000/', // Replace with your API Gateway URL
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
