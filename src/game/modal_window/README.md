# Modal Window (`src/game/modal_window`)

## Overview
Defines the `ModalWindow` value structure used to construct interactive client dialog windows with customizable title, message, buttons, selectable choices, and default Enter/Escape button bindings.

## Interface
- `ModalWindow` (`[modal_window.hpp:ModalWindow]`): Data structure holding `id`, `title`, `message`, `buttons`, `choices`, `defaultEnterButton`, `defaultEscapeButton`, and `priority`.

## Invariants
- `ModalWindow` initializes `defaultEnterButton` and `defaultEscapeButton` to `0xFF` and `priority` to `false` by default (`[modal_window.hpp:ModalWindow::ModalWindow]`).

## Side Effects
- None.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
