# Companion Guide Bot (Interactive Mentor & Quest Navigator)

* **Author:** Daniel Pinheiro Barreto (@dandpb)
* **Date:** 2026-11-11

## Overview

A gameplay companion and interactive tutorial system utilizing the Canary autonomous bot framework. The system provides players with an in-game companion bot that acts as a mentor and guide: leading players through starter zones, demonstrating mechanics (combat, vocation roles, supply management), answering contextual questions via chat, and guiding progression through foundational questlines and level brackets.

## Analysis

### Core Mechanisms Under Consideration

1. **Companion Lifecycle & Recruitment**:
   - Activation through an in-game command (e.g., `/guide` or recruiting via `/party guide`) or automated assignment upon character creation in Rookgaard/Dawnport.
   - Integration with existing `bot_party.cpp` logic for trail-following, leash distance, and support behaviors.

2. **Navigation & Leading (Tutor-Lead vs. Follower)**:
   - **Follower Mode**: Bot follows the player, offering tactical support (heals, buffs) and sending chat tips based on player state (low mana, unequipped gear, low health).
   - **Leader Mode**: Bot uses `botnav` (2D A* and `bot_zgraph` multi-floor transitions) to walk ahead along authored waypoint routes, guiding the player to NPCs, hunting spots, or quest markers.

3. **Knowledge Base & Quest Progression**:
   - Querying player storage values and current quest flags from the engine.
   - Evaluation of deterministic scripted guides (authored CSV/JSON state machines) vs. external pilot brain reasoning (LLM via `botbrain` IPC socket).

### Primary Technical Risks & Friction Points

- **Thread Boundary Invariants**: The bot engine runs on a dedicated dispatcher thread (`libbot_engine.so`). Inspecting player storage, quest flags, or triggering map-wide entity events must avoid data races with the main game thread.
- **LLM vs. Deterministic Scripting**: Using external LLMs introduces inference latency, halluncinated coordinates/quests, and operational costs. Deterministic state machines are exact and free, but require authored data tables for each quest/zone.
- **Player Pacing & Waypoint Desynchronization**: If the guide bot walks ahead into monsters or through floor transitions while the player is trapped, slow, or out of stamina, the guidance loop breaks.

## Goals vs. Non-Goals

### In-Scope Goals
- Allow a solo player to summon or bind a dedicated companion bot that explains game objectives.
- Real-time contextual feedback (e.g., low ammunition, entering dangerous spawns, missing vocation spells).
- Step-by-step navigation guidance to key objectives (temple, bank, depot, starter quests, hunting grounds).
- Party support integration (healing the player, tanking appropriate monsters).

### Out-of-Scope Non-Goals
- Full automation of high-level endgame quests or complex puzzle mechanics requiring human coordination.
- Unrestricted free-form chat answering non-Tibia general knowledge questions.
- Bot replacing human gameplay (bot doing the quest for the player while the player remains AFK).

## Alternatives Weighed

- **Pure OTClient UI Guide Module**:
  - *Description*: Implement client-side arrows, quest trackers, and tutorial popups in OTClient Lua (`modules/game_questlog` or custom module) without any in-game bot creature.
  - *Evaluation*: Lightweight and client-only, but lacks immersive co-op gameplay, dynamic combat assistance, and in-world entity presence.
- **Hardcoded Tutorial NPC**:
  - *Description*: Traditional stationary NPC dialog trees in temples.
  - *Evaluation*: Lacks mobility, cannot travel with the player to dungeons, and cannot adapt to real-time combat situations.

## Key Decisions & Staging for Next Steps

- Defining the primary interaction model (chat-driven vs. command-driven vs. proactive triggers).
- Deciding between deterministic authored quest sequences vs. external pilot brain (LLM IPC).
- Defining failure modes (what happens if the guide bot dies or the player gets lost).
