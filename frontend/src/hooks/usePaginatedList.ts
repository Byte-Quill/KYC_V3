import { useCallback, useEffect, useRef, useState } from "react";
import type { Page } from "../types";

export function usePaginatedList<T>(
  fetcher: (page: number) => Promise<Page<T>>,
  errorMessage = "Failed to load."
) {
  const [items, setItems] = useState<T[]>([]);
  const [count, setCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [pageNum, setPageNum] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Keep the message stable so `load` identity doesn't churn on each render.
  const errorMessageRef = useRef(errorMessage);
  errorMessageRef.current = errorMessage;

  const load = useCallback(async (pageNumber: number) => {
    setLoading(true);
    setError("");
    try {
      const data = await fetcher(pageNumber);
      setItems(data.results);
      setCount(data.count);
      setHasNext(!!data.next);
      setHasPrev(!!data.previous);
    } catch {
      setError(errorMessageRef.current);
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    void load(pageNum);
  }, [load, pageNum]);

  return { items, count, hasNext, hasPrev, pageNum, setPageNum, loading, error };
}
