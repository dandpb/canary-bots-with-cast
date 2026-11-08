# Webhook

## Overview
Provides an asynchronous HTTP POST webhook client backed by `libcurl` and the server `ThreadPool`, primarily used for sending formatted Discord webhook notifications and embeds.

## Interface
- `WebhookTask` (`[webhook.hpp:WebhookTask]`): Struct holding `payload` and `url` strings for queued webhook requests.
- `Webhook` (`[webhook.hpp:Webhook]`): Singleton service (`getInstance()`, `run()`, `sendPayload()`, `sendMessage()`) that queues JSON payloads and dispatches them asynchronously.
- `g_webhook` (`[webhook.hpp:g_webhook]`): `constexpr` accessor alias for `Webhook::getInstance`.

## Invariants
- `Webhook` is non-copyable (`[webhook.hpp:Webhook]`) and synchronizes access to its internal `std::deque<std::shared_ptr<WebhookTask>> webhooks` queue using `std::mutex taskLock` (`[webhook.hpp:Webhook::taskLock]`, `[webhook.cpp:Webhook::sendPayload]`, `[webhook.cpp:Webhook::sendWebhook]`).
- `sendMessage` ignores requests when the target `url` (after falling back to `DISCORD_WEBHOOK_URL`), `message`, or (for embeds) `title` is empty (`[webhook.cpp:Webhook::sendMessage]`).
- In `sendWebhook()`, a task is only popped from the front of `webhooks` when `sendRequest` succeeds with an HTTP status code `< 300`; on `-1`, `429`, `504`, or `>= 300`, the task remains in the queue (`[webhook.cpp:Webhook::sendWebhook]`).

## Side Effects
- Initializes global libcurl state via `curl_global_init(CURL_GLOBAL_ALL)` and allocates `curl_slist` HTTP headers in `Webhook::Webhook` (`[webhook.cpp:Webhook::Webhook]`).
- Performs outbound HTTPS POST network requests (TLSv1.2) using `curl_easy_perform` inside `Webhook::sendRequest` (`[webhook.cpp:Webhook::sendRequest]`).
- Detaches background worker tasks onto `ThreadPool` (`threadPool.detach_task`) and schedules recurring execution ticks on `g_dispatcher()` every `DISCORD_WEBHOOK_DELAY_MS` (`[webhook.cpp:Webhook::run]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
