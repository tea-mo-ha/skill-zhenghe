# Testing Patterns

Reusable testing patterns and anti-patterns across frameworks. Use alongside the main `test-driven-development` skill.

## Setup Patterns

### Test Factories

Build domain objects with sensible defaults and selective overrides:

```typescript
// factory.ts
function buildTask(overrides: Partial<Task> = {}): Task {
  return {
    id: `task-${Math.random().toString(36).slice(2)}`,
    title: 'Test Task',
    status: 'pending',
    ownerId: 'user-1',
    createdAt: new Date('2025-01-01'),
    ...overrides,
  };
}

// Usage
const urgentTask = buildTask({ priority: 'high', dueDate: new Date() });
const doneTask = buildTask({ status: 'completed', completedAt: new Date() });
```

### Fake Implementations

In-memory fakes beat mocks for repository-pattern services:

```typescript
class FakeTaskRepository implements TaskRepository {
  private tasks: Map<string, Task> = new Map();

  async create(task: Task): Promise<Task> {
    this.tasks.set(task.id, task);
    return task;
  }

  async findById(id: string): Promise<Task | null> {
    return this.tasks.get(id) ?? null;
  }

  async findAll(): Promise<Task[]> {
    return Array.from(this.tasks.values());
  }

  // Test helpers (not in the interface)
  _seed(tasks: Task[]): void {
    tasks.forEach(t => this.tasks.set(t.id, t));
  }

  _clear(): void {
    this.tasks.clear();
  }
}
```

## Assertion Patterns

### Custom Matchers

Create domain-specific matchers to improve readability:

```typescript
// jest custom matcher
expect.extend({
  toBeValidTask(received: unknown) {
    const task = received as Task;
    const pass =
      typeof task.id === 'string' &&
      typeof task.title === 'string' &&
      ['pending', 'in-progress', 'completed'].includes(task.status);

    return {
      pass,
      message: () => `expected ${JSON.stringify(received)} to be a valid Task`,
    };
  },
});

// Usage
expect(result).toBeValidTask();
```

### Snapshot Testing (Use Sparingly)

Good use: small, stable output like serialized configs or error messages.

```typescript
// Good: small, meaningful snapshot
it('generates the expected API error response', () => {
  const error = formatApiError(new NotFoundError('Task'));
  expect(error).toMatchInlineSnapshot(`
    {
      "code": "NOT_FOUND",
      "message": "Task not found",
    }
  `);
});
```

Bad use: large component trees, frequently changing UI, or anything reviewers rubber-stamp.

## Async Patterns

### Polling vs. Timers

Never use `setTimeout` in tests. Use polling or deterministic waits:

```typescript
// Good: poll until condition
async function waitFor(fn: () => boolean, timeout = 5000): Promise<void> {
  const start = Date.now();
  while (!fn()) {
    if (Date.now() - start > timeout) throw new Error('Timed out');
    await new Promise(r => setTimeout(r, 50));
  }
}

// Good: fake timers for timer-dependent code
beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

it('debounces search input', () => {
  const onSearch = jest.fn();
  render(<SearchInput onSearch={onSearch} debounce={300} />);

  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } });
  expect(onSearch).not.toHaveBeenCalled();

  jest.advanceTimersByTime(300);
  expect(onSearch).toHaveBeenCalledWith('test');
});
```

### Testing Error Paths

Always test that errors are thrown and caught correctly:

```typescript
it('throws NotFoundError for missing task', async () => {
  await expect(taskService.getTask('nonexistent'))
    .rejects.toThrow(NotFoundError);
});

it('returns 404 for missing resource', async () => {
  const res = await request(app).get('/api/tasks/nonexistent');
  expect(res.status).toBe(404);
  expect(res.body.error.code).toBe('NOT_FOUND');
});
```

## Integration Testing Patterns

### API Route Testing

```typescript
import request from 'supertest';

describe('POST /api/tasks', () => {
  it('creates a task and returns 201', async () => {
    const res = await request(app)
      .post('/api/tasks')
      .send({ title: 'New Task' })
      .expect(201);

    expect(res.body).toMatchObject({
      title: 'New Task',
      status: 'pending',
    });
    expect(res.body.id).toBeDefined();
  });

  it('returns 422 for missing title', async () => {
    const res = await request(app)
      .post('/api/tasks')
      .send({})
      .expect(422);

    expect(res.body.error.code).toBe('VALIDATION_ERROR');
  });
});
```

### Database Testing

Use transactions to isolate tests and roll back after each:

```typescript
let tx: Transaction;

beforeEach(async () => {
  tx = await db.beginTransaction();
});

afterEach(async () => {
  await tx.rollback();
});

it('persists task to database', async () => {
  const task = await taskService.create(tx, { title: 'Test' });
  const found = await taskService.findById(tx, task.id);
  expect(found).toEqual(task);
});
```

## Component Testing Patterns (React)

### Render and Assert

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('toggles task completion', async () => {
  const user = userEvent.setup();
  const onToggle = jest.fn();

  render(<TaskItem task={buildTask()} onToggle={onToggle} />);

  await user.click(screen.getByRole('checkbox'));
  expect(onToggle).toHaveBeenCalledWith(expect.any(String));
});

it('shows empty state when no tasks', () => {
  render(<TaskList tasks={[]} />);
  expect(screen.getByText(/no tasks/i)).toBeInTheDocument();
});
```

### Query Priority

Follow Testing Library's query priority:

1. `getByRole` — accessible name (best)
2. `getByLabelText` — form elements
3. `getByPlaceholderText` — fallback for inputs
4. `getByText` — non-interactive content
5. `getByTestId` — last resort

## Anti-Patterns Reference

| Pattern | Problem | Fix |
|---|---|---|
| `sleep(1000)` in tests | Flaky, slow | Use `waitFor`, fake timers, or poll |
| Mocking what you own | Tests prove nothing | Use real implementation or in-memory fake |
| Testing private methods | Couples to implementation | Test through the public API |
| Shared mutable state | Tests affect each other | Reset state in `beforeEach`/`afterEach` |
| `expect(true).toBe(true)` | Test always passes | Assert on actual output values |
| Ignoring error paths | Happy path only | Test error responses, exceptions, edge cases |
| Large snapshots | Nobody reviews diffs | Use inline snapshots for small, stable output |
| `any` in test types | Hides type errors | Use proper types even in tests |
