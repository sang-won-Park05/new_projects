# integrations/retry.py
from __future__ import annotations

import random
import time
from functools import wraps
from typing import Callable, Iterable, Optional, Tuple, Type, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])

def retry(
    *,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
    tries: int = 2,
    base_delay: float = 0.5,     # 첫 대기 시간(초)
    max_delay: float = 8.0,      # 최대 대기 시간(초)
    jitter: float = 0.2,         # ±지터(초)
    on_retry: Optional[Callable[[int, BaseException], None]] = None,  # 재시도마다 콜백
) -> Callable[[F], F]:
    """
    재시도 데코레이터 (지수 백오프 + 지터).

    Args:
        exceptions: 재시도 대상 예외 타입들 (기본값: Exception)
        tries: 총 시도 횟수 (성공 포함, 최소 1)
        base_delay: 첫 재시도 대기 시간(초). 이후 2배씩 증가.
        max_delay: 대기 상한(초)
        jitter: 대기에 추가되는 무작위 지터(±, 초)
        on_retry: on_retry(attempt, exc) 형태의 콜백. attempt는 1부터 시작.

    Usage:
        @retry(exceptions=(requests.RequestException,), tries=2)
        def fetch(...): ...
    """
    if tries < 1:
        raise ValueError("tries must be >= 1")

    exc_tuple: Tuple[Type[BaseException], ...] = tuple(exceptions)

    def deco(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[misc]
            delay = base_delay
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exc_tuple as e:
                    attempt += 1
                    if attempt >= tries:
                        # 마지막 시도에서도 실패 → 예외 재발생
                        raise
                    # 콜백 호출(로그 등)
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception:
                            # 콜백 실패는 무시
                            pass
                    # 대기 (지수 백오프 + 지터)
                    sleep_s = min(delay, max_delay) + random.uniform(-jitter, jitter)
                    time.sleep(max(0.0, sleep_s))
                    delay = min(delay * 2, max_delay)
        return wrapper  # type: ignore[return-value]
    return deco
