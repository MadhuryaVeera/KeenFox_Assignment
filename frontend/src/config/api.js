export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api';

export const API_HOST = API_BASE_URL.replace(/\/api\/?$/, '');
