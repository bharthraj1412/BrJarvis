# core/di.py — Lightweight Dependency Injection Container for JARVIS MK37
from __future__ import annotations

import inspect
import threading
from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")


class Container:
    """Thread-safe Dependency Injection Container."""
    def __init__(self):
        self._singletons: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
        self._instances: Dict[Type[Any], Any] = {}
        self._lock = threading.RLock()

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register an existing concrete instance as singleton."""
        with self._lock:
            self._instances[interface] = instance

    def register_singleton(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a lazy singleton factory."""
        with self._lock:
            self._factories[interface] = factory
            self._singletons.pop(interface, None)

    def register_transient(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory that creates a new instance on every resolve."""
        with self._lock:
            self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """Resolve an instance for the requested interface or class type."""
        with self._lock:
            # 1. Direct instance registered
            if interface in self._instances:
                return self._instances[interface]

            # 2. Lazy singleton already instantiated
            if interface in self._singletons:
                return self._singletons[interface]

            # 3. Factory registered
            if interface in self._factories:
                instance = self._factories[interface]()
                # Cache if it's singleton registration
                if interface not in self._singletons and interface not in self._instances:
                    self._singletons[interface] = instance
                return instance

            # 4. Auto-instantiation attempt if concrete class with parameterless init
            if inspect.isclass(interface):
                try:
                    instance = interface()
                    self._instances[interface] = instance
                    return instance
                except Exception as e:
                    raise KeyError(f"Could not auto-resolve class {interface.__name__}: {e}")

            raise KeyError(f"No registration found for interface {interface}")

    def clear(self) -> None:
        """Clear all container registrations."""
        with self._lock:
            self._instances.clear()
            self._singletons.clear()
            self._factories.clear()


_global_container = Container()


def get_container() -> Container:
    return _global_container
