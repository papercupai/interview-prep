// Ramp's capture-the-flag challenge, which a Nov-2025 report says also appeared
// in the CodeSignal assessment. Step 1 finds a URL hidden in the DOM; step 2
// fetches it and types the flag out, one list item per character, 500 ms apart,
// with React state only (no CSS, no libraries).
import { useEffect, useState } from 'react';

// Step 1 (run in the console on the challenge page). Ramp rotates the pattern:
// copy YOUR attribute rules into the selector. A space (descendant combinator)
// allows any number of nodes in between; ^= is "starts with", $= "ends with",
// and *= "contains", matching the wildcard positions in the pattern.
export function extractFlagUrl(
  root,
  selector = 'code[data-class^="23"] div[data-tag$="93"] span[data-id*="21"] i.char',
) {
  return [...root.querySelectorAll(selector)].map((el) => el.getAttribute('value')).join('');
}

// Step 2: reveal one more character per tick; stop once the whole string shows.
export function useTypewriter(text, delayMs = 500) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (count >= text.length) return undefined; // plays once, then stops
    const id = setTimeout(() => setCount((n) => n + 1), delayMs);
    return () => clearTimeout(id);
  }, [count, text, delayMs]);
  return text.slice(0, count);
}

function Flag({ text, delayMs }) {
  const shown = useTypewriter(text, delayMs);
  return (
    <ul>
      {[...shown].map((ch, i) => (
        <li key={i}>{ch}</li>
      ))}
    </ul>
  );
}

export default function FlagTypewriter({ url, delayMs = 500 }) {
  const [flag, setFlag] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController(); // StrictMode mounts twice; abort the first request
    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.text();
      })
      .then((text) => setFlag(text.trim()))
      .catch((err) => {
        if (err.name !== 'AbortError') setError(err.message);
      });
    return () => controller.abort();
  }, [url]);

  if (error) return <p role="alert">{error}</p>;
  if (flag === null) return <p>Loading...</p>;
  return <Flag key={flag} text={flag} delayMs={delayMs} />;
}
