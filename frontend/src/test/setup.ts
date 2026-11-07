import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

class Observer { observe() {} unobserve() {} disconnect() {} }
Object.defineProperty(globalThis, 'ResizeObserver', { value: Observer, configurable: true });
Object.defineProperty(window, 'scrollTo', { value: vi.fn(), configurable: true });
vi.mock('uplot', () => ({ default: class { setSize() {} setScale() {} destroy() {} } }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); localStorage.clear(); });
