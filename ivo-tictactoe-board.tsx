// Ivo live coding — the React board on top of ivo-tictactoe.ts. History array = free undo.
import { useState } from "react";
import { newGame, play, isOver, type Game } from "./ivo-tictactoe.ts";

export function TicTacToeBoard({ n = 3, k = n }: { n?: number; k?: number }) {
  const [history, setHistory] = useState<Game[]>(() => [newGame(n, k)]);
  const game = history[history.length - 1];
  const over = isOver(game);

  const status = game.winner ? `${game.winner} wins` : over ? "Draw" : `${game.next} to move`;

  return (
    <div>
      <p role="status">{status}</p>
      <div
        aria-label="Board"
        style={{ display: "grid", gridTemplateColumns: `repeat(${n}, 3rem)`, gap: 4 }}
      >
        {game.board.map((cell, i) => (
          <button
            key={i}
            aria-label={`Row ${Math.floor(i / n) + 1}, column ${(i % n) + 1}`}
            style={{ width: "3rem", height: "3rem", fontSize: "1.5rem" }}
            disabled={cell !== null || over}
            onClick={() => setHistory([...history, play(game, Math.floor(i / n), i % n)])}
          >
            {cell}
          </button>
        ))}
      </div>
      <button disabled={history.length === 1} onClick={() => setHistory(history.slice(0, -1))}>
        Undo
      </button>
      <button onClick={() => setHistory([newGame(n, k)])}>New game</button>
    </div>
  );
}
