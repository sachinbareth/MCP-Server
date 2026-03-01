import random
from fastmcp import FastMCP

# Create a FASTMCP server instance
mcp = FastMCP(name="MCP-Learning")

@mcp.tool
def roll_dice(n_dice: int = 1) -> list[int]:
    """Rolls a number of dice and returns the results."""
    return [random.randint(1, 6) for _ in range(n_dice)]
    
@mcp.tool
def add(a: float, b: float) -> float:
    """Adds two numbers and returns the result."""
    return a + b

if __name__ == "__main__":
    mcp.run() 