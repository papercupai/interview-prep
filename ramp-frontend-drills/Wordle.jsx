// Reported Ramp CodeSignal task: given a secret word, render the board and let
// the user type a guess into an input and submit it with a button.
import { useState } from 'react';

// Two passes, or duplicate letters score wrong: exact matches consume their
// letter first, then "present" may only spend the letters that are left.
export function scoreGuess(secret, guess) {
  const s = secret.toUpperCase();
  const g = guess.toUpperCase();
  const result = Array(g.length).fill('absent');
  const left = {};
  for (let i = 0; i < s.length; i++) {
    if (g[i] === s[i]) result[i] = 'correct';
    else left[s[i]] = (left[s[i]] ?? 0) + 1;
  }
  for (let i = 0; i < g.length; i++) {
    if (result[i] !== 'correct' && left[g[i]] > 0) {
      result[i] = 'present';
      left[g[i]] -= 1;
    }
  }
  return result;
}

const COLOR = { correct: '#6aaa64', present: '#c9b458', absent: '#787c7e' };

export default function Wordle({ secret, maxGuesses = 6 }) {
  const size = secret.length;
  const [guesses, setGuesses] = useState([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  // Derive game state from guesses; storing "won" separately is how it drifts.
  const won = guesses.includes(secret.toUpperCase());
  const over = won || guesses.length >= maxGuesses;

  function submit(event) {
    event.preventDefault();
    const guess = draft.trim().toUpperCase();
    if (guess.length !== size || !/^[A-Z]+$/.test(guess)) {
      setError(`Enter a ${size}-letter word`);
      return;
    }
    setGuesses((prev) => [...prev, guess]);
    setDraft('');
    setError('');
  }

  const rows = Array.from({ length: maxGuesses }, (_, r) => guesses[r] ?? '');
  return (
    <div>
      <div role="grid" aria-label="board">
        {rows.map((word, r) => {
          const states = word ? scoreGuess(secret, word) : [];
          return (
            <div role="row" key={r} style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
              {Array.from({ length: size }, (_, c) => (
                <div
                  role="gridcell"
                  key={c}
                  data-state={states[c] ?? 'empty'}
                  style={{ width: 40, height: 40, display: 'grid', placeItems: 'center', border: '1px solid #999', background: COLOR[states[c]] ?? 'white' }}
                >
                  {word[c] ?? ''}
                </div>
              ))}
            </div>
          );
        })}
      </div>
      {!over && (
        <form onSubmit={submit}>
          <input aria-label="guess" value={draft} maxLength={size} onChange={(e) => setDraft(e.target.value)} />
          <button type="submit">Submit</button>
        </form>
      )}
      {error && <p role="alert">{error}</p>}
      {won && <p>You win!</p>}
      {over && !won && <p>The word was {secret.toUpperCase()}</p>}
    </div>
  );
}
