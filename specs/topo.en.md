# Topology notes

Technology process:

- Bipolar transistors
- A single metal layer (m1)
- Only two cell types: logic cells (implement the basic gates `not`, `nor`) and
  peripheral cells (for the terminals / pads).

## Routing grid (mesh)

Connections between cells are routed with the single metal layer (m1). The EDA
tool that was used placed all the "nodes" on a grid:

![cell1](/imgstore/cell1.png) ![cell2](/imgstore/cell2.png)

For path finding (router) over free nodes the A* or Dijkstra algorithm was most
likely used.

Some wires could jump over nodes diagonally.
