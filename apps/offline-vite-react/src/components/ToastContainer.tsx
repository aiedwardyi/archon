import React, { useState, useEffect } from "react";

type Toast = {
  id: number;
  message: string;
  type: "success" | "error" | "info";
};

let toastId = 0;
const toastListeners: Array<(toast: Toast) => void> = [];

export function showToast(message: string, type: "success" | "error" | "info" = "info") {
  const toast: Toast = { id: toastId++, message, type };
  toastListeners.forEach((listener) => listener(toast));
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (toast: Toast) => {
      setToasts((prev) => [...prev, toast]);
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 5000);
    };

    toastListeners.push(listener);
    
    return () => {
      const idx = toastListeners.indexOf(listener);
      if (idx > -1) toastListeners.splice(idx, 1);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: "fixed",
      top: 20,
      right: 20,
      zIndex: 99999,
      display: "flex",
      flexDirection: "column",
      gap: 10,
    }}>
      {toasts.map((toast) => (
        <div
          key={toast.id}
          style={{
            padding: "16px 24px",
            borderRadius: 8,
            background: toast.type === "error" ? "#dc2626" : toast.type === "success" ? "#16a34a" : "#2563eb",
            color: "white",
            boxShadow: "0 8px 24px rgba(0,0,0,0.3)",
            fontSize: 16,
            fontWeight: 600,
            maxWidth: 400,
            minWidth: 250,
            animation: "slideIn 0.3s ease-out",
            border: "2px solid white",
          }}
        >
          {toast.message}
        </div>
      ))}
    </div>
  );
}
