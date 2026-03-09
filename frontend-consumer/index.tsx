import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';

function bootstrapSession() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');

  if (!token) return;

  localStorage.setItem('archon_token', token);
  params.delete('token');
  params.delete('switch');

  const remaining = params.toString();
  const nextUrl = remaining ? `${window.location.pathname}?${remaining}` : window.location.pathname;
  window.history.replaceState({}, '', nextUrl);
}

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

async function mount() {
  bootstrapSession();
  const { default: App } = await import('./App');
  const root = ReactDOM.createRoot(rootElement);

  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

void mount();
