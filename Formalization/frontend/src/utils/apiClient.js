import axios from 'axios';

console.log('🚀 [VERBOSE] API Client module loading...');

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

console.log('🔧 [VERBOSE] API Client Configuration:', {
  API_BASE_URL,
  environment: process.env.NODE_ENV,
  reactAppApiUrl: process.env.REACT_APP_API_URL
});

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes timeout
});

console.log('✅ [VERBOSE] API Client created with baseURL:', apiClient.defaults.baseURL);

// Add request interceptor to automatically include auth token
apiClient.interceptors.request.use(
  (config) => {
    console.log('🌐 [VERBOSE] API Request Interceptor - Outgoing request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      headers: config.headers,
      timeout: config.timeout,
      data: config.data instanceof FormData ? 'FormData (files)' : config.data
    });
    
    // Get token from localStorage
    const token = localStorage.getItem('bear_systems_token');
    console.log('🔐 [VERBOSE] Auth token from localStorage:', token ? 'Present' : 'Not found');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ [VERBOSE] Authorization header added to request');
    } else {
      console.log('⚠️ [VERBOSE] No auth token found, proceeding without Authorization header');
    }
    
    console.log('📤 [VERBOSE] Final request config:', {
      method: config.method,
      url: config.url,
      headers: config.headers,
      hasData: !!config.data
    });
    
    return config;
  },
  (error) => {
    console.error('❌ [VERBOSE] Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => {
    console.log('📥 [VERBOSE] API Response Interceptor - Incoming response:', {
      status: response.status,
      statusText: response.statusText,
      url: response.config?.url,
      method: response.config?.method?.toUpperCase(),
      headers: response.headers,
      dataType: typeof response.data,
      dataSize: response.data ? JSON.stringify(response.data).length : 0
    });
    console.log('📦 [VERBOSE] Response data preview:', response.data);
    return response;
  },
  (error) => {
    console.error('❌ [VERBOSE] API Response Interceptor - Error response:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      responseData: error.response?.data,
      code: error.code
    });
    
    if (error.response?.status === 401) {
      console.log('🔒 [VERBOSE] 401 Unauthorized - Clearing token and redirecting to login');
      // Token is invalid or expired
      localStorage.removeItem('bear_systems_token');
      delete axios.defaults.headers.common['Authorization'];
      
      // Redirect to login or trigger logout
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;

// Add a health check function for debugging
export const testConnection = async () => {
  console.log('🔍 [VERBOSE] Testing API connection...');
  try {
    const response = await apiClient.get('/health');
    console.log('✅ [VERBOSE] API health check successful:', response.data);
    return { success: true, data: response.data };
  } catch (error) {
    console.error('❌ [VERBOSE] API health check failed:', error);
    return { success: false, error: error.message };
  }
};

// Test connection on module load (only in development)
if (process.env.NODE_ENV === 'development') {
  setTimeout(() => {
    testConnection();
  }, 1000);
}
