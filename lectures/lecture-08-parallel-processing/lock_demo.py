import threading
import time


ITERATIONS = 2_000
THREAD_COUNT = 4


def increment_unsafe(counter: list) -> None:
    for _ in range(ITERATIONS):
        current = counter[0]
        time.sleep(0)
        counter[0] = current + 1


def increment_safe(counter: list, lock: threading.Lock) -> None:
    for _ in range(ITERATIONS):
        with lock:
            current = counter[0]
            time.sleep(0)
            counter[0] = current + 1


def run(target, *args) -> int:
    counter = [0]

    threads = [
        threading.Thread(
            target=target,
            args=(counter, *args),
        )
        for _ in range(THREAD_COUNT)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return counter[0]


def main() -> None:
    expected = ITERATIONS * THREAD_COUNT

    unsafe_result = run(increment_unsafe)
    print(
        f"Lock-ის გარეშე: {unsafe_result:,} "
        f"(მოსალოდნელი: {expected:,})"
    )

    lock = threading.Lock()
    safe_result = run(increment_safe, lock)
    print(
        f"Lock-ით:        {safe_result:,} "
        f"(მოსალოდნელი: {expected:,})"
    )


if __name__ == "__main__":
    main()