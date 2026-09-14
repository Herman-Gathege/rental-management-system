// frontend/src/hooks/useDebouncedValue.jsx
//
// Small debounce hook used by the searchable tables and the global palette, so
// typing doesn't fire one request per keystroke.

import { useEffect, useState } from "react";

export function useDebouncedValue(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(handle);
  }, [value, delay]);

  return debounced;
}

export default useDebouncedValue;
