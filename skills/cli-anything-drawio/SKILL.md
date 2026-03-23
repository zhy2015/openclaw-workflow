---
name: cli-anything-drawio
description: Use CLI-Anything to generate professional diagrams (architecture, flowcharts, logic trees) via Draw.io. Trigger this when the user asks to "draw a diagram", "generate architecture", or "画个流程图/架构图". 
metadata: {"clawdbot":{"emoji":"📊"}}
---

# CLI-Anything Draw.io Diagram Generator

This skill enables the agent to programmatically generate professional diagrams without manual XML editing, using the `cli-anything-drawio` harness and headles Draw.io.

## Prerequisites
- `cli-anything-drawio` python package is installed in the environment.
- `drawio` desktop app and `Xvfb` are installed on the host.

## Workflow

When the user asks for a diagram, follow these steps using `exec`:

### 1. Initialize Project
Create a temporary directory and initialize a new drawio project.
```bash
mkdir -p /tmp/drawio_gen
cli-anything-drawio project new -o /tmp/drawio_gen/diagram.drawio
```

### 2. Add Shapes (Nodes)
Identify the key components of the user's request and add shapes.
Supported shapes: `rectangle`, `rounded`, `ellipse`, `diamond`, `cylinder`, `cloud`, `actor`, `process`, `document`, `note`.

```bash
cli-anything-drawio --project /tmp/drawio_gen/diagram.drawio shape add actor -l "User" --x 100 --y 200
cli-anything-drawio --project /tmp/drawio_gen/diagram.drawio shape add cloud -l "API Gateway" --x 300 --y 180 -w 140 -h 100
```
*(Note: Keep track of the generated node IDs in the stdout, e.g., `v_1773245252784520`)*

### 3. Connect Shapes (Edges)
Use the IDs generated in Step 2 to connect the components.
```bash
cli-anything-drawio --project /tmp/drawio_gen/diagram.drawio connect add <source_id> <target_id> -l "Request"
```

### 4. Render to PNG
Use `xvfb-run` to headlessly render the `.drawio` XML into a `.png` image.
```bash
xvfb-run drawio --no-sandbox -x -f png -o /tmp/drawio_gen/diagram.png /tmp/drawio_gen/diagram.drawio
```

### 5. Deliver to User
If communicating via QQBot, DO NOT use the `message` tool. Instead, directly output the `<qqimg>` tag in your chat response.
```text
这是为您生成的架构图：
<qqimg>/tmp/drawio_gen/diagram.png</qqimg>
```

## Design Best Practices
- **Spacing**: Ensure sufficient X and Y spacing between nodes (e.g., 200px horizontally).
- **Alignment**: Align logically related nodes on the same Y-axis.
- **Size**: Default width is usually 120, height 60. For databases (`cylinder`), 80x100 looks better.
