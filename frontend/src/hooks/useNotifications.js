import { useCallback, useEffect, useState } from "react";
import { api, endpoints } from "../services/api";
import { useAuth } from "../context/AuthContext";

/** Polls the unread badge count — kept in one place so every surface agrees. */
export function useNotificationCount(intervalMs = 45000) {
  const { isAuthenticated } = useAuth();
  const [count, setCount] = useState(0);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setCount(0);
      return;
    }
    try {
      const data = await api.get(endpoints.unreadCount);
      setCount(data?.count ?? 0);
    } catch {
      // A failed poll should not break navigation; the next tick retries.
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refresh();
    if (!isAuthenticated) return undefined;
    const timer = setInterval(refresh, intervalMs);
    return () => clearInterval(timer);
  }, [refresh, isAuthenticated, intervalMs]);

  return { count: isAuthenticated ? count : 0, refresh };
}
