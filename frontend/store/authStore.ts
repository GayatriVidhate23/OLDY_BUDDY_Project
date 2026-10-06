export interface UserSession {
  id: number;
  email: string;
  fullName?: string;
  role: 'ELDER' | 'CAREGIVER' | 'FAMILY' | 'ADMIN';
}

type Listener = () => void;

class AuthStore {
  private user: UserSession | null = null;
  private token: string | null = null;
  private listeners: Set<Listener> = new Set();

  subscribe(listener: Listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((l) => l());
  }

  setUser(user: UserSession | null, token: string | null = null) {
    this.user = user;
    if (token) this.token = token;
    this.notify();
  }

  getUser(): UserSession | null {
    return this.user;
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  logout() {
    this.user = null;
    this.token = null;
    this.notify();
  }
}

export const authStore = new AuthStore();
