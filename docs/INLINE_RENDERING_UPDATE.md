# Inline/Sequential Rendering Update

## Overview
Implemented chronological/inline rendering for tool calls and thinking indicators in the chat UI. Elements now appear **in the order they occur** during the conversation, rather than being grouped at the top.

## What Changed

### Before (Grouped)
```
[All Tool Calls Grouped at Top]
[Thinking at Top]
[Response Text at Bottom]
```

### After (Inline/Sequential)
```
[Text Chunk 1]
[Tool Call 1]
[Tool Call 2]  
[Text Chunk 2]
[Thinking...]
[Text Chunk 3]
```

## Technical Changes

### 1. New Tracking Variable
- Added `currentTextBlock` to track the active text block for inline flow
- When a tool call or thinking indicator interrupts, `currentTextBlock` is set to `null`
- Next text creates a new block that appears after the interruption

### 2. Modified Functions

#### `thinking_start` Handler
- Changed from `prepend()` to `appendChild()` 
- Thinking indicators now append inline, before `.message-actions` if present
- Sets `currentTextBlock = null` to force new text block after

#### `tool_start` Handler  
- Now calls `addToolCallInline()` instead of `addToolCall()`
- Sets `currentTextBlock = null` to force new text block after

#### `addToolCallInline()` (NEW)
- Appends tool calls directly to message content inline
- No longer uses `.tool-calls-container` grouping
- Each tool call is an independent inline element

#### `updateAssistantMessageText()`
- Completely rewritten for inline flow
- Creates new text blocks on demand when `currentTextBlock` is null
- Reuses existing text block for streaming updates

#### `createAssistantMessage()`
- Removed pre-created `.message-text` div
- Content now built dynamically as elements arrive

### 3. CSS Updates
- Added `.inline-element` class with proper margins
- Tool calls and thinking indicators use this for spacing
- Ensures clean visual separation between elements

## Result
The chat now displays tool calls and thinking indicators **exactly where they happen** in the conversation flow, matching the user's expectation for a natural, chronological display.
