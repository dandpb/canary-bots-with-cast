# Messaging (`src/lib/messaging`)

## Overview

The `src/lib/messaging` component provides lightweight, header-only typed message, command, and event dispatching primitives built on top of `eventpp::EventDispatcher` and `eventpp::ScopedRemover`.

## Interface

- `[message.hpp:Message]` — Template struct `Message<T>` wrapping an enum/tag `type` of type `T`.
- `[message.hpp:MessageHandler]` / `[message.hpp:MessagePolicy]` / `[message.hpp:MessageDispatcher]` / `[message.hpp:MessageRemover]` — Type aliases and policy wiring `Message<T>` into `eventpp::EventDispatcher` and `eventpp::ScopedRemover`.
- `[message.hpp:IMessageListener]` / `[message.hpp:MessageListeners]` — Abstract listener interface (`setupListeners(MessageDispatcher<T> &dispatcher)`) and `std::vector<std::shared_ptr<IMessageListener<T>>>` collection alias.
- `[command.hpp:CommandType]` — Lifecycle command enumeration (`start`, `load`, `run`, `shutdown`).
- `[command.hpp:ICommand]` / `[command.hpp:CommandHandler]` / `[command.hpp:CommandPolicy]` / `[command.hpp:CommandListener]` / `[command.hpp:CommandListeners]` / `[command.hpp:CommandDispatcher]` / `[command.hpp:CommandRemover]` / `[command.hpp:command]` — Command specialization of `Message<CommandType>` and helper macros `commandCallback` and `appendCommandListener`.
- `[event.hpp:EventType]` / `[event.hpp:IEvent]` / `[event.hpp:EventHandler]` / `[event.hpp:EventPolicy]` / `[event.hpp:EventListener]` / `[event.hpp:EventListeners]` / `[event.hpp:EventDispatcher]` / `[event.hpp:EventRemover]` / `[event.hpp:event]` — Event specialization of `Message<EventType>` and helper macros `eventCallback` and `appendEventListener`.

## Invariants

- `[message.hpp:MessagePolicy::getEvent]` — Dispatch routing key is strictly `msg.type`.

## Side Effects

- `None`

## Verification

- Run: `ctest --test-dir build --output-on-failure`
