# Dependency Injection (`src/lib/di`)

## Overview

The `src/lib/di` component provides the Dependency Injection (DI) infrastructure for Canary, built on top of `boost::di`. It manages object instantiation, singleton/shared lifetimes, runtime provider bindings for testing (`di::extension::runtime_injector`), and soft-singleton instance tracking (`SoftSingleton` / `SoftSingletonGuard`) to bridge legacy global accessors (`g_*()`) with constructor/field injection and testability.

## Interface

- `[container.hpp:DI]` — Static facade managing `defaultContainer` (binding `AccountRepository` to `AccountRepositoryDB`, `KVStore` to `KVSQL`, and `Logger` to `LogWithSpdLog` in `di::singleton` scope) and an optional `testContainer` (`setTestContainer`, `getTestContainer`, `create<T>()`, `get<T>()`).
- `[container.hpp:inject]` — Global helper `inject<Type>()` delegating to `DI::get<Type>()` for contextual/field injection.
- `[injector.hpp:boost::di::extension::injector]` — Variadic injector template specializing `injector<>` as `runtime_injector`.
- `[runtime_provider.hpp:boost::di::extension::runtime_provider]` — Dynamic type-indexed binding provider (`bindings()`, `data<T>()`, `provider(...)`) with `assert_error_policy`.
- `[runtime_provider.hpp:boost::di::extension::runtime_injector]` — Alias for `detail::injector<assert_error_policy, di::extension::shared_config>` supporting `install(...)` of bindings at runtime.
- `[shared.hpp:boost::di::extension::shared]` / `[shared.hpp:boost::di::extension::shared_config]` — Thread-safe (unless `BOOST_DI_NOT_THREAD_SAFE` is defined) shared scope configuration mapping `T&`, `std::shared_ptr<T>`, `boost::shared_ptr<T>`, and `std::weak_ptr<T>` to shared instances.
- `[soft_singleton.hpp:SoftSingleton]` — Tracks active instance counts (`increment()`, `decrement()`) for soft-singleton types and logs a warning if multiple instances coexist.
- `[soft_singleton.hpp:SoftSingletonGuard]` — RAII guard that increments a `SoftSingleton` on construction and decrements it on destruction.

## Invariants

- `[container.hpp:DI::get]` — Always resolves `T&` (`create<T&>()`), returning a shared singleton instance managed by the active container (`testContainer` if non-null, otherwise `defaultContainer`).
- `[runtime_provider.hpp:boost::di::extension::assert_error_policy::error]` — Requesting an unbound abstract or non-constructible type from `runtime_provider` triggers `assert(false && "Type not bound!")`.
- `[soft_singleton.cpp:SoftSingleton::increment]` — Emits a warning via `g_logger().warn(...)` whenever `instance_count > 1`.
- `[soft_singleton.hpp:SoftSingleton]` / `[soft_singleton.hpp:SoftSingletonGuard]` — Both classes are non-copyable (`= delete` copy constructor and copy assignment).

## Side Effects

- `[container.hpp:DI::setTestContainer]` — Mutates the process-wide static pointer `DI::testContainer`, redirecting all subsequent `DI::create`, `DI::get`, and `inject` calls.
- `[shared.hpp:boost::di::extension::detail::shared::scope::create]` — Acquires a `std::mutex` lock (when `BOOST_DI_NOT_THREAD_SAFE` is not defined) and lazily allocates `std::shared_ptr<T>` in the scope or provider `data_` map.
- `[soft_singleton.cpp:SoftSingleton::increment]` — Mutates `instance_count` and logs warnings through `Logger` (`g_logger()`).

## Verification

- Run: `ctest --test-dir build --output-on-failure`

---

## Dependency Injection Guide

Dependency injection is a technique for achieving loose coupling between objects and their collaborators, or dependencies. It is a form of inversion of control, where the control being inverted is the setting of object's dependencies.

### Container

A container is a place where dependencies are stored. It is responsible for creating objects and injecting their dependencies.
It is also responsible for managing the lifetime of objects it creates.

In [boost::di](https://boost-ext.github.io/di/), the container is represented by the `di::injector` class.
It is a variadic template class that takes a list of modules as template parameters.
A module is a class that defines how to create objects and how to inject their dependencies.
A module can be a class or a lambda function. 

#### Getting an Instance of a Type

To get an instance of a type, we call the `create` method of the container.

The default injector created from the `di::make_injector` function can create instances of types that weren't registered, if they are concrete types.

For interfaces, we have to register a provider for the interface.
For instance:
```cpp
class A {
public:
    virtual ~A() = default;
};

class B : public A {};

auto container = di::make_injector(
    di::bind<A>().to<B>()
);
auto a = container.create<A>();
auto a = container.create<B>();
```

Both injections above create an instance of `B`, one through the interface `A` and one directly.

#### Scopes

A scope is a way to manage the lifetime of an object.
There are two main types of scopes in our use cases:  

**Unique**

Unique scope creates a new instance of an object every time it is requested.
It is the default scope when calling the `create` method of the container.

For instance:
```cpp
auto container = di::make_injector(
    di::bind<Logger>().to<LogWithSpdLog>()
);
auto logger1 = container.create<Logger &>();
auto logger2 = container.create<Logger &>();
```

In the example above, `logger1` and `logger2` are different instances of `LogWithSpdLog`.

**Shared (Singleton)**  

Singleton scope creates a single instance of an object and returns it every time it is requested.
It is the default scope when registering a provider via reference or shared pointer.

For instance:
```cpp
auto container = di::make_injector(
    di::bind<Logger>().to<LogWithSpdLog>()
);
auto logger1 = container.create<Logger &>();
auto logger2 = container.create<Logger &>();
```

In the example above, `logger1` and `logger2` are the same instance of `LogWithSpdLog`.

### Injection

Injection is the process of providing dependencies to an object.
It is done by the container when it creates an object.

#### Constructor Injection

Constructor injection is the process of providing dependencies to an object through its constructor.
For instance:
```cpp
class A {
public:
    A(int i, double d) {}
};

class B {
public:
    B(A a) {}
};

class C {
public:
    C(A a) {}
};

auto container = di::make_injector();
auto a = container.create<A &>();
auto b = container.create<B &>();
auto c = container.create<C>();
```

In the example above, the container creates an instance of `A` and injects it into the constructors of `B` and `C`.
When the container creates an instance of `B`, it creates an instance of `A` and passes it to the constructor of `B`.
When the container creates an instance of `C`, it creates an instance of `A` and passes it to the constructor of `C`.

#### Field Injection

Field injection is the process of providing dependencies to an object through its fields.
For instance:
```cpp
class A {
public:
    int i;
    double d;
};

class B {
public:
    A &a = inject<A>();
};

auto container = di::make_injector();
auto a = container.create<A &>();
auto b = container.create<B &>();
B b2{};
```

In the example above, the container creates an instance of `A` and injects it into the field `a` of `B`.
When the container creates an instance of `B`, it creates an instance of `A` and assigns it to the field `a` of `B`.
When we create an instance of `B` manually, we have to call the `inject` function to inject an instance of `A` into the field `a` of `B`.

#### Global Variables

Our code base relies on global variables g_() that behaves like singletons.
When we moved to DependencyInjection we've migrated those singletons to the container.
For instance:
```cpp
Logger LogWithSpdLog::getInstance() {
    return inject<Logger>();
}

constexpr auto g_logger = LogWithSpdLog::getInstance;
```

In the example above, we've created a provider for the `Logger` interface.
We've also created a global variable `g_logger` that is initialized with an instance of `Logger` from the container.
Every time we call `g_logger`, we get the same instance of `Logger`.

They are somewhat softer than the traditional singletons, because we can still create instances of them manually.
That improves our testability, because we can create stubs of the `Logger` interface and inject it into the container.


### Using the Container

To simplify the registration of providers in singleton scope, we've created three auxiliary functions.

#### `DI::create<T>`

This translates directly to container.create<T>() and can return unique or shared instances, depending on the value of T.

#### `DI::get<T>`

This translates directly to container.create<T &>() and will always return the same instance.

#### `inject<T>()`

This is a shortcut for `DI::get<T>()` and is used to inject dependencies into fields of objects that are not created by the container.


### Testing

For tests, we allow the setup of a test container via the `DI::setTestContainer` function.
This function receives an instace of `di::injector` and sets it as the test container.
When the test container is set, the `DI::create<T>` and `DI::get<T>` functions will return instances from the test container.
When the test container is not set, the `DI::create<T>` and `DI::get<T>` functions will return instances from the default container.

This gives us the ability to create stubs of interfaces and inject them into the container for testing.
That way we are able to test the behavior of our code without having to rely on the implementation of the dependencies.

For instance:
```cpp
{
    di::extension::injector<> injector{};
    DI::setTestContainer(&InMemoryLogger::install(injector));

    auto &logger = dynamic_cast<InMemoryLogger &>(injector.create<Logger &>());
    auto &logger2 = dynamic_cast<InMemoryLogger &>(inject<Logger>());
    auto &logger3 = g_logger();
}
```

In the example above, we've created a test container and registered a provider for the `Logger` interface.
Because the test container is set, the `DI::create<T>` and `DI::get<T>` functions will return instances from the test container.
When we call `DI::create<Logger &>()`, we get an instance of `InMemoryLogger`.
When we call `DI::get<Logger &>()`, we get the same instance of `InMemoryLogger`.
When we call `g_logger()`, we get the same instance of `InMemoryLogger`.
