from abc import ABC, abstractmethod
from threading import Lock

from visual_underwriting.config import Settings


class ImageHashStore(ABC):
    @abstractmethod
    def record_if_new(self, image_hash: str) -> bool:
        """Return True when the hash was not previously seen and has been stored."""


class InMemoryImageHashStore(ImageHashStore):
    def __init__(self) -> None:
        self._seen_hashes: set[str] = set()
        self._lock = Lock()

    def record_if_new(self, image_hash: str) -> bool:
        with self._lock:
            if image_hash in self._seen_hashes:
                return False
            self._seen_hashes.add(image_hash)
            return True


class RedisImageHashStore(ImageHashStore):
    def __init__(self, redis_url: str, key_prefix: str, ttl_seconds: int | None = None) -> None:
        from redis import Redis

        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def record_if_new(self, image_hash: str) -> bool:
        key = f"{self._key_prefix}:{image_hash}"
        was_set = self._redis.set(key, "1", nx=True, ex=self._ttl_seconds)
        return bool(was_set)


def build_image_hash_store(settings: Settings) -> ImageHashStore:
    if settings.image_hash_storage.lower() == "redis":
        return RedisImageHashStore(
            redis_url=settings.redis_url,
            key_prefix=settings.redis_key_prefix,
            ttl_seconds=settings.redis_hash_ttl_seconds,
        )

    return InMemoryImageHashStore()
