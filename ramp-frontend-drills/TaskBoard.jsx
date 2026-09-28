// CodeSignal Front-End Development Framework, worked end to end.
// This is CodeSignal's own published example (a task board, 4 levels).
// One component carries all four levels; comments mark where each level lands.
import { useEffect, useRef, useState } from 'react';

const API = 'https://contentapi.codesignal.com';

// Column order drives Level 4 (move left/right). Render the status text exactly
// as the template does: the grader reads the DOM, not your intentions.
export const COLUMNS = ['TO_DO', 'IN_PROGRESS', 'DONE'];

// Level 1: the static JSON arrives grouped by column. Flatten it into ONE list
// with a status field so levels 2-4 only ever touch one array.
export function fromStaticJson(data) {
  return [...data.todoItems, ...data.inProgressItems, ...data.doneItems].map((task, i) => ({
    id: `static-${i}`,
    ...task,
    user: null,
  }));
}

// Level 3: /tasks is flat but names need a second, dependent call per user.
// Fetch each distinct user once, in parallel; one missing user must not blank the board.
export async function loadTasks(fetchImpl = fetch) {
  const res = await fetchImpl(`${API}/tasks`);
  if (!res.ok) throw new Error(`GET /tasks failed: ${res.status}`);
  const { data } = await res.json();
  const ids = [...new Set(data.map((t) => t.assignedUser).filter(Boolean))];
  const users = await Promise.all(
    ids.map(async (id) => {
      const r = await fetchImpl(`${API}/users/${id}`);
      return r.ok ? r.json() : null;
    }),
  );
  const byId = Object.fromEntries(users.filter(Boolean).map((u) => [u.id, u]));
  return data.map((t, i) => ({ id: `task-${i}`, ...t, user: byId[t.assignedUser] ?? null }));
}

export default function TaskBoard({ load = loadTasks }) {
  const [tasks, setTasks] = useState([]);
  const [status, setStatus] = useState('loading');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const nextId = useRef(0);

  useEffect(() => {
    let cancelled = false; // ignore a response that lands after unmount
    load()
      .then((loaded) => {
        if (!cancelled) {
          setTasks(loaded);
          setStatus('ready');
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  // Level 2: controlled inputs; a new task always starts in TO_DO.
  function addTask(event) {
    event.preventDefault();
    if (!title.trim() || !description.trim()) return; // both fields are required (*)
    nextId.current += 1;
    const task = { id: `new-${nextId.current}`, title: title.trim(), description: description.trim(), status: 'TO_DO', user: null };
    setTasks((prev) => [...prev, task]);
    setTitle('');
    setDescription('');
  }

  // Level 4: move one column left/right; the moved card goes to the bottom of its new column.
  function move(id, step) {
    setTasks((prev) => {
      const task = prev.find((t) => t.id === id);
      const next = COLUMNS.indexOf(task.status) + step;
      if (next < 0 || next >= COLUMNS.length) return prev;
      return [...prev.filter((t) => t.id !== id), { ...task, status: COLUMNS[next] }];
    });
  }

  return (
    <div className="board">
      <h2 className="board__title">Tasks</h2>
      <form onSubmit={addTask}>
        <div className="input-container">
          <input name="taskTitle" placeholder="Task title*" value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="input-container">
          <textarea name="taskDescription" placeholder="Task description*" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div>
          <input type="submit" value="Create task" />
        </div>
      </form>
      {status === 'loading' && <p>Loading...</p>}
      {status === 'error' && <p role="alert">Could not load tasks.</p>}
      <div className="board__columns">
        {COLUMNS.map((column, ci) => (
          <div className="column" key={column}>
            <h2 className="column__title">{column}</h2>
            <div className="column__cards">
              {tasks
                .filter((t) => t.status === column)
                .map((t) => (
                  <div className="card" key={t.id}>
                    <h3 className="card__title">{t.title}</h3>
                    <p className="card__description">{t.description}</p>
                    {t.user && (
                      <p className="card__user">
                        {t.user.firstName} {t.user.lastName}
                      </p>
                    )}
                    <div className="card__buttons">
                      {ci > 0 && (
                        <button aria-label="button left" className="card__button card__button--left" type="button" onClick={() => move(t.id, -1)} />
                      )}
                      {ci < COLUMNS.length - 1 && (
                        <button aria-label="button right" className="card__button card__button--right" type="button" onClick={() => move(t.id, 1)} />
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
