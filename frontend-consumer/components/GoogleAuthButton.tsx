import React, { useEffect, useRef, useState } from 'react';

type GoogleButtonText = 'signin_with' | 'signup_with' | 'continue_with';

interface GoogleCredentialResponse {
  credential?: string;
}

interface GoogleIdApi {
  initialize: (config: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
    ux_mode?: 'popup' | 'redirect';
  }) => void;
  renderButton: (
    parent: HTMLElement,
    options: {
      theme?: 'outline' | 'filled_black' | 'filled_blue';
      size?: 'large' | 'medium' | 'small';
      shape?: 'rectangular' | 'pill' | 'circle' | 'square';
      text?: GoogleButtonText;
      width?: number;
      logo_alignment?: 'left' | 'center';
    }
  ) => void;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: GoogleIdApi;
      };
    };
  }
}

interface GoogleAuthButtonProps {
  text?: GoogleButtonText;
  onCredential: (credential: string) => Promise<void> | void;
  onError: (message: string) => void;
}

const GOOGLE_CLIENT_ID =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ||
  '1094133324705-0dgm6o9cu0oud74l0im9l4ncsvlvknka.apps.googleusercontent.com';

let googleScriptPromise: Promise<void> | null = null;

function loadGoogleScript() {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  if (googleScriptPromise) {
    return googleScriptPromise;
  }

  googleScriptPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-google-identity]');
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error('Google sign-in is unavailable right now.')), {
        once: true,
      });
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = 'true';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Google sign-in is unavailable right now.'));
    document.head.appendChild(script);
  });

  return googleScriptPromise;
}

const GoogleAuthButton: React.FC<GoogleAuthButtonProps> = ({ text = 'continue_with', onCredential, onError }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const mountButton = async () => {
      try {
        await loadGoogleScript();
        if (cancelled || !containerRef.current || !window.google?.accounts?.id) {
          return;
        }

        containerRef.current.innerHTML = '';
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          ux_mode: 'popup',
          callback: (response) => {
            const credential = response.credential;
            if (!credential) {
              onError('No Google credential received');
              return;
            }
            void Promise.resolve(onCredential(credential)).catch((error: unknown) => {
              onError(error instanceof Error ? error.message : 'Google sign-in failed');
            });
          },
        });
        window.google.accounts.id.renderButton(containerRef.current, {
          theme: 'filled_black',
          size: 'large',
          shape: 'pill',
          text,
          width: Math.max(containerRef.current.clientWidth, 280),
          logo_alignment: 'left',
        });
        if (!cancelled) {
          setReady(true);
        }
      } catch (error) {
        if (!cancelled) {
          onError(error instanceof Error ? error.message : 'Google sign-in is unavailable right now.');
        }
      }
    };

    void mountButton();

    return () => {
      cancelled = true;
    };
  }, [onCredential, onError, text]);

  return (
    <div className="w-full">
      {!ready && (
        <div className="mb-3 flex min-h-[44px] items-center justify-center rounded-[1.2rem] border border-white/10 bg-white/[0.05] text-sm text-white/60">
          Loading Google...
        </div>
      )}
      <div ref={containerRef} className={ready ? 'w-full' : 'sr-only'} />
    </div>
  );
};

export default GoogleAuthButton;
