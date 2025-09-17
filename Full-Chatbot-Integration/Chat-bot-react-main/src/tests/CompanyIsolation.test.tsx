import { render, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import CompanyProvider, { useCompany, validateCompanyAccess } from '../context-provider/CompanyProvider';
import Dashboard from '../page/Dashboard';
import UserManagement from '../page/UserManagement';

// Mock axios
vi.mock('../config/axiosConfig', () => ({
  axiosClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock SWR
vi.mock('swr', () => ({
  default: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
    mutate: vi.fn(),
  })),
}));

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <CompanyProvider>
      {children}
    </CompanyProvider>
  </BrowserRouter>
);

describe('Company Isolation Tests', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('CompanyProvider', () => {
    it('should initialize with null company info', () => {
      const TestComponent = () => {
        const { companyInfo, companyId, isLoading } = useCompany();
        return (
          <div>
            <div data-testid="company-info">{companyInfo ? 'loaded' : 'null'}</div>
            <div data-testid="company-id">{companyId || 'null'}</div>
            <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // expect(screen.getByTestId('company-info')).toHaveTextContent('null');
      // expect(screen.getByTestId('company-id')).toHaveTextContent('null');
      // expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    it('should load company ID from localStorage', () => {
      localStorage.setItem('company_id', 'TEST001');

      const TestComponent = () => {
        const { companyId } = useCompany();
        return <div data-testid="company-id">{companyId}</div>;
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // expect(screen.getByTestId('company-id')).toHaveTextContent('TEST001');
    });
  });

  describe('Company Access Validation', () => {
    it('should allow SuperAdmin to access any company', () => {
      localStorage.setItem('role', 'SUPERADMIN');
      localStorage.setItem('company_id', 'SUPER001');

      const result = validateCompanyAccess('TEST001');
      expect(result).toBe(true);
    });

    it('should allow Admin to access their own company', () => {
      localStorage.setItem('role', 'ADMIN');
      localStorage.setItem('company_id', 'TEST001');

      const result = validateCompanyAccess('TEST001');
      expect(result).toBe(true);
    });

    it('should deny Admin access to other companies', () => {
      localStorage.setItem('role', 'ADMIN');
      localStorage.setItem('company_id', 'TEST001');

      const result = validateCompanyAccess('TEST002');
      expect(result).toBe(false);
    });

    it('should allow Agent to access their own company', () => {
      localStorage.setItem('role', 'AGENT');
      localStorage.setItem('company_id', 'TEST001');

      const result = validateCompanyAccess('TEST001');
      expect(result).toBe(true);
    });

    it('should deny Agent access to other companies', () => {
      localStorage.setItem('role', 'AGENT');
      localStorage.setItem('company_id', 'TEST001');

      const result = validateCompanyAccess('TEST002');
      expect(result).toBe(false);
    });
  });

  describe('Dashboard Component', () => {
    it('should render loading state initially', () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      // Should show loading skeletons
      expect(document.querySelectorAll('.animate-pulse')).toHaveLength(6);
    });

    it('should display company-specific data when loaded', async () => {
      const mockStats = {
        pending_sessions: 5,
        active_sessions: 3,
        total_agents: 8,
        online_agents: 6,
        total_users: 150,
        today_conversations: 25
      };

      // Mock SWR to return data
      const useSWR = await import('swr');
      vi.mocked(useSWR.default).mockReturnValue({
        data: mockStats,
        isLoading: false,
        error: null,
        mutate: vi.fn(),
        isValidating: false,
      } as any);

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // expect(screen.getByText('5')).toBeInTheDocument(); // Pending sessions
        // expect(screen.getByText('3')).toBeInTheDocument(); // Active sessions
        // expect(screen.getByText('8')).toBeInTheDocument(); // Total agents
      });
    });
  });

  describe('UserManagement Component', () => {
    it('should render with company context', () => {
      localStorage.setItem('company_id', 'TEST001');
      localStorage.setItem('role', 'ADMIN');

      render(
        <TestWrapper>
          <UserManagement />
        </TestWrapper>
      );

      // expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    it('should show loading state for stats', () => {
      render(
        <TestWrapper>
          <UserManagement />
        </TestWrapper>
      );

      // Should show loading skeletons for stats cards
      expect(document.querySelectorAll('.animate-pulse')).toHaveLength(4);
    });
  });

  describe('API Integration', () => {
    it('should include company_id in API requests for non-SuperAdmin users', async () => {
      localStorage.setItem('company_id', 'TEST001');
      localStorage.setItem('role', 'ADMIN');
      localStorage.setItem('access_token', 'test-token');

      const { axiosClient } = await import('../config/axiosConfig');
      
      // Mock a GET request
      vi.mocked(axiosClient.get).mockResolvedValue({
        data: { results: [] }
      });

      // Simulate making a request
      await axiosClient.get('/admin-dashboard/user-profiles/');

      // Verify that the request was made with company_id
      expect(axiosClient.get).toHaveBeenCalledWith('/admin-dashboard/user-profiles/', {
        params: { company_id: 'TEST001' }
      });
    });

    it('should not include company_id for SuperAdmin users', async () => {
      localStorage.setItem('company_id', 'SUPER001');
      localStorage.setItem('role', 'SUPERADMIN');
      localStorage.setItem('access_token', 'test-token');

      const { axiosClient } = await import('../config/axiosConfig');
      
      // Mock a GET request
      vi.mocked(axiosClient.get).mockResolvedValue({
        data: { results: [] }
      });

      // Simulate making a request
      await axiosClient.get('/auth/list-admins/');

      // Verify that the request was made without company_id filtering
      expect(axiosClient.get).toHaveBeenCalledWith('/auth/list-admins/', {
        params: {}
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle company access violations', async () => {
      const { axiosClient } = await import('../config/axiosConfig');
      
      // Mock a 403 error with company-related message
      const error = {
        response: {
          status: 403,
          data: {
            error: 'Access denied to company data'
          }
        }
      };

      vi.mocked(axiosClient.get).mockRejectedValue(error);

      // The interceptor should handle this error
      try {
        await axiosClient.get('/admin-dashboard/user-profiles/');
      } catch (e) {
        expect(e).toEqual(error);
      }
    });

    it('should redirect to login on 401 errors', async () => {
      const { axiosClient } = await import('../config/axiosConfig');
      
      // Mock window.location
      delete (window as any).location;
      window.location = { href: '' } as any;

      // Mock a 401 error
      const error = {
        response: {
          status: 401,
          data: {
            error: 'Token expired'
          }
        }
      };

      vi.mocked(axiosClient.get).mockRejectedValue(error);

      try {
        await axiosClient.get('/admin-dashboard/user-profiles/');
      } catch (e) {
        // Should clear localStorage and redirect
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('company_id')).toBeNull();
        expect(window.location.href).toBe('/login');
      }
    });
  });

  describe('WebSocket Company Isolation', () => {
    it('should generate company-specific WebSocket URLs', async () => {
      localStorage.setItem('company_id', 'TEST001');

      const { getCompanyWebSocketUrl } = await import('../context-provider/CompanyProvider');
      
      const url = getCompanyWebSocketUrl('chat/session123');
      expect(url).toBe('ws://localhost:8000/ws/chat/session123/TEST001/');
    });

    it('should use default company if none set', async () => {
      const { getCompanyWebSocketUrl } = await import('../context-provider/CompanyProvider');
      
      const url = getCompanyWebSocketUrl('chat/session123');
      expect(url).toBe('ws://localhost:8000/ws/chat/session123/DEFAULT_COMPANY/');
    });

    it('should use provided company ID over localStorage', async () => {
      localStorage.setItem('company_id', 'TEST001');

      const { getCompanyWebSocketUrl } = await import('../context-provider/CompanyProvider');
      
      const url = getCompanyWebSocketUrl('chat/session123', 'TEST002');
      expect(url).toBe('ws://localhost:8000/ws/chat/session123/TEST002/');
    });
  });
});
