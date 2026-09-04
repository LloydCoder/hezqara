"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect } from "react";
import { setApiTokenProvider } from "@/lib/api";

export function AuthBridge() {
  const { getToken } = useAuth();

  useEffect(() => {
    setApiTokenProvider(getToken);
    return () => setApiTokenProvider(null);
  }, [getToken]);

  return null;
}
