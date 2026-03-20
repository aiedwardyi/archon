import React, { useEffect, useState } from 'react';

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
  prompt: (
    momentListener?: (notification: {
      isNotDisplayed?: () => boolean;
      isSkippedMoment?: () => boolean;
      getNotDisplayedReason?: () => string;
      getSkippedReason?: () => string;
    }) => void
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
  '975672204403-a1tbslh4raerh7tlrdgepr19qlnvvlmk.apps.googleusercontent.com';

let googleScriptPromise: Promise<void> | null = null;

function getButtonLabel(text: GoogleButtonText) {
  if (text === 'signin_with') return 'Sign in with Google';
  if (text === 'signup_with') return 'Sign up with Google';
  return 'Continue with Google';
}

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
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const initializeGoogle = async () => {
      try {
        await loadGoogleScript();
        if (cancelled || !window.google?.accounts?.id) {
          return;
        }

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
        if (!cancelled) {
          setReady(true);
        }
      } catch (error) {
        if (!cancelled) {
          onError(error instanceof Error ? error.message : 'Google sign-in is unavailable right now.');
        }
      }
    };

    void initializeGoogle();

    return () => {
      cancelled = true;
    };
  }, [onCredential, onError]);

  const handleClick = () => {
    if (!ready || !window.google?.accounts?.id) {
      onError('Google sign-in is unavailable right now.');
      return;
    }

    window.google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed?.() || notification.isSkippedMoment?.()) {
        onError(
          notification.getNotDisplayedReason?.() ||
            notification.getSkippedReason?.() ||
            'Google sign-in is unavailable right now.'
        );
      }
    });
  };

  return (
    <div className="w-full">
      {!ready && (
        <div className="flex min-h-[50px] items-center justify-center rounded-[1.4rem] border border-white/10 bg-white/[0.05] text-sm text-white/60">
          Loading Google...
        </div>
      )}
      {ready && (
        <button
          type="button"
          onClick={handleClick}
          className="w-full flex items-center justify-center gap-3 rounded-[1.4rem] border border-white/10 bg-white/[0.05] px-4 py-3 text-sm font-medium text-white transition hover:bg-white/[0.08]"
        >
          <svg aria-hidden="true" viewBox="0 0 18 18" className="h-[18px] w-[18px] flex-shrink-0">
            <path
              fill="#4285F4"
              d="M17.64 9.2045c0-.6382-.0573-1.2518-.1636-1.8409H9v3.4818h4.8436c-.2087 1.125-.8432 2.0782-1.7987 2.715v2.2582h2.9087c1.7018-1.5668 2.6864-3.8741 2.6864-6.6141Z"
            />
            <path
              fill="#34A853"
              d="M9 18c2.43 0 4.4673-.8068 5.9564-2.1818l-2.9087-2.2582c-.8068.54-1.8382.8591-3.0477.8591-2.3441 0-4.3282-1.5832-5.0364-3.7105H.9573v2.3291C2.4382 15.9818 5.4818 18 9 18Z"
            />
            <path
              fill="#FBBC05"
              d="M3.9636 10.7086A5.4093 5.4093 0 0 1 3.6818 9c0-.5932.1014-1.1686.2818-1.7086V4.9623H.9573A8.9994 8.9994 0 0 0 0 9c0 1.4523.3477 2.8277.9573 4.0377l3.0063-2.3291Z"
            />
            <path
              fill="#EA4335"
              d="M9 3.5795c1.3214 0 2.5077.4541 3.4418 1.3459l2.5814-2.5813C13.4632.8918 11.4259 0 9 0 5.4818 0 2.4382 2.0182.9573 4.9623l3.0063 2.3291C4.6718 5.1627 6.6559 3.5795 9 3.5795Z"
            />
          </svg>
          <span>{getButtonLabel(text)}</span>
        </button>
      )}
    </div>
  );
};

export default GoogleAuthButton;
