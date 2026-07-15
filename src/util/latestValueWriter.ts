type AsyncWriter<T> = (value: T) => Promise<unknown>;
type Snapshot<T> = (value: T) => T;

interface PendingValue<T> {
  value: T;
  version: number;
}

interface Waiter {
  version: number;
  resolve: () => void;
  reject: (error: unknown) => void;
}

/**
 * Serializes writes while coalescing values that have not started writing yet.
 * Every caller settles after its value, or a newer value, has been written.
 */
export class LatestValueWriter<T> {
  private pending: PendingValue<T> | undefined;
  private running = false;
  private scheduled = false;
  private nextVersion = 0;
  private waiters: Waiter[] = [];

  constructor(
    private readonly writer: AsyncWriter<T>,
    private readonly snapshot: Snapshot<T> = (value) => value,
  ) {}

  enqueue(value: T): Promise<void> {
    const version = ++this.nextVersion;
    this.pending = {
      value: this.snapshot(value),
      version,
    };

    const completion = this.waitFor(version);
    this.schedule();
    return completion;
  }

  flush(): Promise<void> {
    if (!this.pending && !this.running && !this.scheduled) {
      return Promise.resolve();
    }
    return this.waitFor(this.nextVersion);
  }

  private waitFor(version: number): Promise<void> {
    return new Promise((resolve, reject) => {
      this.waiters.push({ version, resolve, reject });
    });
  }

  private schedule(): void {
    if (this.running || this.scheduled) {
      return;
    }

    this.scheduled = true;
    void Promise.resolve().then(() => {
      this.scheduled = false;
      return this.drain();
    });
  }

  private async drain(): Promise<void> {
    if (this.running) {
      return;
    }

    this.running = true;
    try {
      while (this.pending) {
        const current = this.pending;
        this.pending = undefined;

        try {
          await this.writer(current.value);
          this.settleThrough(current.version, false);
        } catch (error) {
          this.settleThrough(current.version, true, error);
        }
      }
    } finally {
      this.running = false;
      if (this.pending) {
        this.schedule();
      }
    }
  }

  private settleThrough(
    version: number,
    failed: boolean,
    error?: unknown,
  ): void {
    const remaining: Waiter[] = [];
    for (const waiter of this.waiters) {
      if (waiter.version > version) {
        remaining.push(waiter);
      } else if (failed) {
        waiter.reject(error);
      } else {
        waiter.resolve();
      }
    }
    this.waiters = remaining;
  }
}
