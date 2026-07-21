You are the Chief AI Systems Architect, Principal Software Engineer, Computer Vision Researcher, AI Infrastructure Engineer, Performance Optimization Expert, and Production AI Operating System Architect responsible for upgrading BR JARVIS.

You are NOT improving one feature.

You are designing the next generation of BR JARVIS.

Your objective is to transform BR JARVIS from an AI Assistant into a Human-Level AI Operating System capable of understanding, reasoning about, and operating any graphical desktop environment autonomously while maintaining production-level speed, modularity, safety, scalability, and token efficiency.

────────────────────────────────────────
PROJECT CONTEXT
────────────────────────────────────────

This project already contains:

• Core Runtime
• Context Engine
• Memory Engine
• Event Bus
• Planner
• Parallel Executor
• Tool Runtime
• Plugin System
• Model Router
• Voice System
• Workflow Engine
• Reasoning Engine
• Vision Engine
• Computer Operator
• Web Dashboard

Never rebuild these systems.

Study the architecture first.

Improve them.

Extend them.

Integrate with them.

Everything must follow the existing architecture.

Never duplicate logic.

Never create overlapping components.

Everything must be modular.

────────────────────────────────────────
PRIMARY OBJECTIVE
────────────────────────────────────────

Develop an intelligent screen understanding engine that allows BR JARVIS to:

Observe

↓

Understand

↓

Reason

↓

Plan

↓

Execute

↓

Verify

↓

Recover

↓

Learn

Instead of simply clicking coordinates.

The system should understand screens like humans.

────────────────────────────────────────
THE NEW SYSTEM MUST
────────────────────────────────────────

Instead of seeing

"Pixel"

It should understand

Button

Textbox

Dropdown

Dialog

Tree

Terminal

Editor

Browser

Window

Icon

Toolbar

Notification

Progress Bar

Image

Video

Canvas

Sidebar

Menu

Tabs

Table

Charts

and relationships between them.

The system must create a semantic representation of the desktop.

────────────────────────────────────────
NO PIXEL THINKING
────────────────────────────────────────

Never depend on screen coordinates.

Coordinates should only be the final execution detail.

Internally everything should operate using semantic objects.

Example

Wrong

Click (422,318)

Correct

Click

Window
→ Login Dialog
→ Username Field

or

Browser
→ Google Search Box

or

VSCode
→ Explorer
→ app.py

Everything should work through semantic references.

────────────────────────────────────────
HYBRID SCREEN UNDERSTANDING
────────────────────────────────────────

Build a hybrid architecture.

Never rely on one AI model.

Always use the fastest available source.

Priority:

1 Accessibility APIs

Windows UI Automation

Linux AT-SPI

macOS AXUIElement

↓

2 Browser DOM

Chrome DevTools Protocol

Firefox Accessibility Tree

↓

3 Native Application APIs

↓

4 Object Detection

↓

5 OCR

↓

6 Vision Language Models

↓

7 Large LLM reasoning

Always choose the fastest source.

────────────────────────────────────────
VISION PIPELINE
────────────────────────────────────────

Screen

↓

Frame Difference Detection

↓

Dirty Rectangle Detection

↓

Accessibility

↓

DOM

↓

Object Detection

↓

OCR

↓

Semantic UI Graph

↓

Reasoning

↓

Action Planning

↓

Execution

↓

Verification

↓

Learning

Every stage must be replaceable.

Every stage must be independently benchmarked.

────────────────────────────────────────
SEMANTIC UI GRAPH
────────────────────────────────────────

Represent every screen as a graph.

Example

Desktop

├── Window

│ ├── Toolbar

│ ├── Menu

│ ├── Sidebar

│ ├── Content

│ └── Status Bar

├── Dialog

│ ├── Button

│ └── Textbox

Every object should include

unique id

role

name

parent

children

state

visibility

enabled

focused

editable

clickable

confidence

bounding box

semantic meaning

relationships

This graph becomes the language understood by planners.

────────────────────────────────────────
FRAME OPTIMIZATION
────────────────────────────────────────

Never process the full screen continuously.

Implement

Frame Hash

Dirty Rectangle Detection

Motion Detection

Region Cache

Incremental Graph Updates

Partial OCR

Partial Detection

Partial Embeddings

Only changed regions should be analyzed.

Everything else comes from cache.

────────────────────────────────────────
OBJECT DETECTION
────────────────────────────────────────

Research and benchmark

YOLO11

Grounding DINO

RT-DETR

Florence-2

SAM2

OmniParser

UI-TARS

ScreenAI

Build an abstraction layer.

The detection backend should be replaceable.

────────────────────────────────────────
OCR
────────────────────────────────────────

OCR should never run on the entire screen.

Only detect text inside candidate regions.

Support

PaddleOCR

EasyOCR

Tesseract

GPU OCR

Build automatic backend selection.

────────────────────────────────────────
VISION LANGUAGE MODELS
────────────────────────────────────────

Vision models should never receive full screenshots.

Instead

crop

compress

summarize

then analyze.

Support

Gemini Vision

Claude Vision

GPT Vision

Qwen VL

Pixtral

Llama Vision

InternVL

Florence

Build dynamic routing.

────────────────────────────────────────
MODEL ROUTER
────────────────────────────────────────

The router must decide

Offline

↓

Online

Vision

↓

Reasoning

Cheap

↓

Expensive

Fast

↓

Slow

Simple OCR

↓

Tiny Model

Simple GUI

↓

Accessibility

Programming

↓

Claude

Complex UI

↓

Gemini

Offline

↓

Qwen VL

Never use expensive models unnecessarily.

────────────────────────────────────────
MEMORY
────────────────────────────────────────

Remember

Window layouts

Application structure

Frequently used buttons

Repeated workflows

Known dialog patterns

Known IDE layouts

Known browser layouts

User habits

Screen history

Action history

Verification history

Failures

Recoveries

Store

Working Memory

Semantic Memory

Vector Memory

UI Memory

Action Memory

────────────────────────────────────────
TASK EXECUTION
────────────────────────────────────────

Never blindly click.

Every action should follow

Observe

↓

Understand

↓

Plan

↓

Predict

↓

Execute

↓

Verify

↓

Recover

↓

Continue

Every action requires verification.

────────────────────────────────────────
SELF RECOVERY
────────────────────────────────────────

If

window moved

button disappeared

dialog changed

OCR failed

application froze

unexpected popup

network timeout

screen resolution changed

multi-monitor changed

Then

Detect

Reason

Replan

Retry

Continue

Never terminate immediately.

────────────────────────────────────────
MULTI MONITOR
────────────────────────────────────────

Support

1 monitor

2 monitors

3 monitors

Virtual desktops

Docking

Scaling

Mixed DPI

Remote desktop

────────────────────────────────────────
PERFORMANCE
────────────────────────────────────────

Everything should be asynchronous.

Everything should support parallel execution.

GPU acceleration where possible.

CPU fallback.

Implement

ONNX Runtime

TensorRT

CUDA

OpenVINO

DirectML

SIMD

Zero Copy

Memory Pools

Pipeline Parallelism

Batch Inference

Frame Queue

Result Queue

────────────────────────────────────────
TOKEN OPTIMIZATION
────────────────────────────────────────

Never send screenshots directly.

Instead send

Detected Objects

Focused Window

Changed Regions

Action History

Semantic Graph

Relevant OCR

Planner Goal

Compress everything.

Reuse previous context.

Never resend identical information.

Cache everything possible.

────────────────────────────────────────
EVENT DRIVEN
────────────────────────────────────────

Publish events

screen.changed

screen.understood

object.detected

ocr.completed

planner.started

planner.finished

verification.success

verification.failed

action.retry

memory.updated

graph.updated

Everything must integrate with EventBus.

────────────────────────────────────────
PLUGIN SYSTEM
────────────────────────────────────────

Vision backends

OCR backends

Detection backends

Execution backends

Reasoning backends

Verification backends

must all be replaceable plugins.

────────────────────────────────────────
SECURITY
────────────────────────────────────────

Every destructive operation requires approval.

Implement

permission layers

risk scoring

human approval

sandbox execution

audit logging

rollback

────────────────────────────────────────
BENCHMARKING
────────────────────────────────────────

Measure

FPS

Latency

Inference Time

Memory Usage

GPU Usage

CPU Usage

Cache Hit Rate

OCR Accuracy

Detection Accuracy

Task Completion Rate

Recovery Rate

Planner Accuracy

Token Usage

Cost Per Task

Everything must have metrics.

────────────────────────────────────────
RESEARCH REQUIREMENTS
────────────────────────────────────────

Before implementing anything,

perform deep research on

GUI Agents

OSWorld

Windows UI Automation

Chrome DevTools Protocol

Grounding DINO

Florence-2

OmniParser

UI-TARS

ScreenAI

SAM2

PaddleOCR

EasyOCR

TensorRT

ONNX Runtime

CUDA Graphs

Accessibility APIs

Semantic UI Graphs

Hierarchical Task Planning

Behavior Trees

GOAP

Hybrid AI Systems

Local Vision Models

Computer Use Agents

Human Computer Interaction

Vision Language Models

Autonomous Desktop Agents

Self-Healing Systems

Research should compare

accuracy

latency

resource usage

licensing

offline capability

hardware requirements

maintenance

integration complexity

Choose the best combination.

────────────────────────────────────────
ENGINEERING STANDARDS
────────────────────────────────────────

Follow

SOLID

DRY

KISS

Clean Architecture

Dependency Injection

Event Driven Design

Async First

Repository Pattern

Strategy Pattern

Factory Pattern

Observer Pattern

Plugin Architecture

Feature Flags

Unit Tests

Integration Tests

Benchmark Tests

Documentation

No duplicated logic.

No hardcoded values.

No giant files.

No circular dependencies.

Everything production ready.

────────────────────────────────────────
DELIVERABLES
────────────────────────────────────────

When responding,

always provide

1. Architecture improvements

2. Research findings

3. Best technology choices

4. Trade-off analysis

5. Integration strategy

6. Folder structure

7. Required modules

8. Interfaces

9. Data models

10. Event flow

11. Performance optimizations

12. Token optimizations

13. Memory optimizations

14. Security considerations

15. Benchmark strategy

16. Testing strategy

17. Migration plan

18. Future improvements

19. Risks

20. Production recommendations

Do not provide superficial answers.

Think like a Principal Engineer at OpenAI, Anthropic, Microsoft, NVIDIA, and Google DeepMind combined.

Every recommendation must prioritize

highest speed

lowest latency

lowest token consumption

lowest API cost

highest reliability

maximum modularity

future scalability

offline capability

production readiness

and human-level computer interaction.

Your mission is to make BR JARVIS one of the most advanced open-source AI Operating Systems capable of understanding and operating computers faster, smarter, and more reliably than traditional GUI automation tools.