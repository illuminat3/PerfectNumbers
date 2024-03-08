import threading
import json
from pathlib import Path
import subprocess
import time

def pull_latest_files():
    subprocess.run(["git", "pull"], check=True)

def git_commit_and_push(message):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Changes committed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to commit and push changes: {e}")

def periodic_commit(stop_signal):
    while not stop_signal['stop']:
        git_commit_and_push("Periodic commit of results and state.")
        time.sleep(600)  # Wait for 10 minutes before next commit

def is_perfect(n):
    if n < 2:
        return False
    if n % 2 == 1:
        return False
    p = 1
    while True:
        p *= 2
        if (2**p - 1) * (2**(p-1)) == n:
            return is_prime(p) and is_prime(2**p - 1)
        if (2**p - 1) * (2**(p-1)) > n:
            break
    sum_divisors = 1
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            sum_divisors += i
            if i != n // i:
                sum_divisors += n // i
    return sum_divisors == n

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def search_perfect_numbers(start, step, lock, stop_signal, state):
    current = start
    while not stop_signal['stop']:
        if is_perfect(current):
            with lock:
                print(f"Found perfect number: {current}")
                with open('results.txt', 'a') as f:
                    f.write(f"{current}\n")
                current = current * 2
        else:
            print (current)
        with lock:
            state['current'] = current
        current += step

def init_state():
    state_path = Path('state.json')
    if state_path.exists():
        try:
            with open('state.json', 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {'current': 0}
    else:
        return {'current': 0}

def simulate_keypress(stop_signal):
    input("Press Enter to stop...")
    git_commit_and_push("updated result and state")
    stop_signal['stop'] = True

if __name__ == "__main__":
   # pull_latest_files()
    num_threads = 6
    threads = []
    lock = threading.Lock()
    state = init_state()
    stop_signal = {'stop': False}
    start_value = state.get('current', 0) + 1

    open('results.txt', 'a').close()

    periodic_commit_thread = threading.Thread(target=periodic_commit, args=(stop_signal,))
    periodic_commit_thread.start()

    keypress_thread = threading.Thread(target=simulate_keypress, args=(stop_signal,))
    keypress_thread.start()

    for i in range(num_threads):
        adjusted_start = start_value + i
        thread = threading.Thread(target=search_perfect_numbers, args=(adjusted_start, num_threads, lock, stop_signal, state))
        threads.append(thread)
        thread.start()

    keypress_thread.join()

    for thread in threads:
        thread.join()

    stop_signal['stop'] = True
    periodic_commit_thread.join()

    with open('state.json', 'w') as f:
        json.dump(state, f)

    git_commit_and_push("Final commit of results and state.")
    print("Search complete.")
