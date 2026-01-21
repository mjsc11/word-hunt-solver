cat > README.md << 'EOF'
# Word Hunt Solver (iMessage / Boggle-style)

Solves NxN Word Hunt boards using 8-direction adjacency (like Boggle).
No cell can be reused within the same word.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
