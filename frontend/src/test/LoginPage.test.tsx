import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import LoginPage from '../components/LoginPage';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    img: (props: any) => <img {...props} />,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('LoginPage', () => {
  const mockLogin = vi.fn().mockResolvedValue(true);

  it('renders username and password fields', () => {
    render(<LoginPage onLogin={mockLogin} loading={false} error={null} />);
    expect(screen.getByPlaceholderText(/seunome/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('******')).toBeInTheDocument();
  });

  it('renders login button', () => {
    render(<LoginPage onLogin={mockLogin} loading={false} error={null} />);
    expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument();
  });

  it('shows error message when error prop is set', () => {
    render(<LoginPage onLogin={mockLogin} loading={false} error="E-mail ou senha incorretos" />);
    expect(screen.getByText(/incorretos/i)).toBeInTheDocument();
  });

  it('disables button while loading', () => {
    render(<LoginPage onLogin={mockLogin} loading={true} error={null} />);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
  });

  it('calls onLogin with username and password on submit', async () => {
    const user = userEvent.setup();
    render(<LoginPage onLogin={mockLogin} loading={false} error={null} />);

    const emailInput = screen.getByPlaceholderText(/seunome/i);
    const passwordInput = screen.getByPlaceholderText('******');

    await user.type(emailInput, 'adalbertobaptista');
    await user.type(passwordInput, 'MyPassword1');
    await user.click(screen.getByRole('button', { name: /entrar/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('adalbertobaptista', 'MyPassword1');
    });
  });

  it('renders brand title', () => {
    render(<LoginPage onLogin={mockLogin} loading={false} error={null} />);
    expect(screen.getByText('SCOUTING BFSA')).toBeInTheDocument();
  });
});
