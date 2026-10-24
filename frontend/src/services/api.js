const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMsg = typeof errorData.detail === 'string' 
              ? errorData.detail 
              : JSON.stringify(errorData.detail);
          }
        } catch {
          // ignore json parse error
        }
        throw new Error(errorMsg);
      }
      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(
          `Unable to connect to WindScope backend API at ${API_BASE_URL}. Ensure the backend service is running on port 8000.`
        );
      }
      throw error;
    }
  }

  async getHealth() {
    return this.request('/api/health');
  }

  async getCutoffs() {
    return this.request('/api/forecasts/cutoffs');
  }

  async getAnalysis({ cutoffType = 'd1_1200', customCutoff = null, alignment = 'exact', startDate = null, endDate = null } = {}) {
    const params = new URLSearchParams();
    if (cutoffType) params.append('cutoff_type', cutoffType);
    if (customCutoff) params.append('custom_cutoff', customCutoff);
    if (alignment) params.append('alignment', alignment);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    return this.request(`/api/analysis?${params.toString()}`);
  }

  async getVintages(deliveryTime, cutoffType = 'd1_1200', customCutoff = null) {
    const params = new URLSearchParams();
    params.append('delivery_time', deliveryTime);
    if (cutoffType) params.append('cutoff_type', cutoffType);
    if (customCutoff) params.append('custom_cutoff', customCutoff);

    return this.request(`/api/forecasts/vintages?${params.toString()}`);
  }

  async getDataQuality() {
    return this.request('/api/data-quality');
  }

  async refreshData() {
    return this.request('/api/analysis/refresh', { method: 'POST' });
  }
}

export const api = new ApiService();
