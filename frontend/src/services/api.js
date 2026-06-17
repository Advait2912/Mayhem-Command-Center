const API_BASE = 'http://localhost:8000';

export const api = {
  async generateReport(eventData) {
    try {
      const response = await fetch(`${API_BASE}/api/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData),
      });
      if (!response.ok) throw new Error('Network response was not ok');
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
};
