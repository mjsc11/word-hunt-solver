cat > web/app.js <<'EOF'
function scoreWord(word) {
  const n = word.length;
  if (n < 3) return 0;
  if (n <= 4) return 1;
  if (n === 5) return 2;
  if (n === 6) return 3;
  if (n === 7) return 5;
  return 11;
}

class TrieNode {
  constructor() {
    this.children = new Map();
    this.isWord = false;
  }
}

class Trie {
  constructor() {
    this.root = new TrieNode();
  }
  insert(word) {
    let node = this.root;
    for (const ch of word) {
      if (!node.children.has(ch)) node.children.set(ch, new TrieNode());
      node = node.children.get(ch);
    }
    node.isWord = true;
  }
}

function parseGrid(text, size) {
  const s = text.trim().toLowerCase();
  if (s.includes("\n")) {
    const lines = s.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
    if (lines.length !== size) throw new Error(`Expected ${size} rows, got ${lines.length}.`);
    const grid = [];
    for (const ln of lines) {
      const row = ln.includes(" ")
        ? ln.split(/\s+/).filter(Boolean)
        : [...ln].filter(ch => /[a-z]/.test(ch));
      if (row.length !== size) throw new Error(`Each row must have ${size} letters: "${ln}"`);
      grid.push(row);
    }
    return grid;
  }
  // compact
  const compact = [...s].filter(ch => /[a-z]/.test(ch)).join("");
  if (compact.length !== size * size) throw new Error(`Expected ${size*size} letters, got ${compact.length}.`);
  const grid = [];
  for (let r=0; r<size; r++) {
    grid.push(compact.slice(r*size, (r+1)*size).split(""));
  }
  return grid;
}

function neighbors(r, c, rows, cols) {
  const out = [];
  for (let dr=-1; dr<=1; dr++) {
    for (let dc=-1; dc<=1; dc++) {
      if (dr===0 && dc===0) continue;
      const nr = r+dr, nc = c+dc;
      if (nr>=0 && nr<rows && nc>=0 && nc<cols) out.push([nr,nc]);
    }
  }
  return out;
}

function solveWithPaths(grid, trie, minLen) {
  const rows = grid.length, cols = grid[0].length;
  const visited = Array.from({length: rows}, () => Array(cols).fill(false));
  const results = new Map(); // word -> path

  function dfs(r, c, node, current, path) {
    visited[r][c] = true;
    const ch = grid[r][c];
    const nextNode = node.children.get(ch);
    if (!nextNode) {
      visited[r][c] = false;
      return;
    }

    const nextWord = current + ch;
    path.push([r,c]);

    if (nextWord.length >= minLen && nextNode.isWord) {
      if (!results.has(nextWord)) results.set(nextWord, path.slice());
    }

    for (const [nr,nc] of neighbors(r,c,rows,cols)) {
      if (!visited[nr][nc]) dfs(nr,nc,nextNode,nextWord,path);
    }

    path.pop();
    visited[r][c] = false;
  }

  for (let r=0; r<rows; r++) {
    for (let c=0; c<cols; c++) {
      dfs(r,c,trie.root,"",[]);
    }
  }
  return results;
}

function renderResults(items, showPaths, oneBased) {
  if (items.length === 0) return `<p class="muted">No words found (or dictionary not loaded).</p>`;
  const rows = items.map(({word, score, path}) => {
    const pathStr = showPaths
      ? `<span class="mono">${path.map(([r,c]) => oneBased ? `(${r+1},${c+1})` : `(${r},${c})`).join("->")}</span>`
      : "";
    return `<tr>
      <td class="mono">${score}</td>
      <td class="mono">${word}</td>
      <td class="mono">${word.length}</td>
      <td>${pathStr}</td>
    </tr>`;
  }).join("");

  return `<table>
    <thead>
      <tr><th>Score</th><th>Word</th><th>Len</th><th>Path</th></tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

async function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(fr.result);
    fr.onerror = reject;
    fr.readAsText(file);
  });
async function loadDictionaryText(minLen) {
  // 1) If user uploaded a file, use it
     const file = document.getElementById("dictFile").files[0];
     if (file) return await readFileAsText(file);

  // 2) If user pasted words, use that
     const pasted = (document.getElementById("dictText")?.value || "").trim();
     if (pasted.length > 0) return pasted;

  // 3) Otherwise, fetch the built-in dictionary shipped with the site
     const res = await fetch("./words.txt", { cache: "no-store" });
     if (!res.ok) throw new Error("Could not load built-in words.txt. (Is it in docs/?)");
     return await res.text();
}

}

document.getElementById("clearBtn").addEventListener("click", () => {
  document.getElementById("results").innerHTML = "";
  document.getElementById("status").textContent = "";
});

document.getElementById("solveBtn").addEventListener("click", async () => {
  const status = document.getElementById("status");
  const resultsDiv = document.getElementById("results");

  try {
    const size = Number(document.getElementById("size").value);
    const minLen = Number(document.getElementById("minLen").value);
    const minScore = Number(document.getElementById("minScore").value);
    const topN = Number(document.getElementById("topN").value);
    const showPaths = document.getElementById("paths").checked;
    const oneBased = document.getElementById("oneBased").checked;

    const gridText = document.getElementById("grid").value;
    const grid = parseGrid(gridText, size);

    status.textContent = "Loading built-in dictionary...";
    const res = await fetch("./words.txt", { cache: "no-store" });
    if (!res.ok) throw new Error("Missing built-in words.txt in /docs");
    const dictText = await res.text();



    status.textContent = `Building trie (${words.length.toLocaleString()} words)...`;
    const trie = new Trie();
    for (const w of words) trie.insert(w);

    status.textContent = "Solving...";
    const found = solveWithPaths(grid, trie, minLen); // Map word->path

    let items = [];
    for (const [word, path] of found.entries()) {
      const sc = scoreWord(word);
      if (sc >= minScore) items.push({word, score: sc, path});
    }

    items.sort((a,b) => (b.score - a.score) || (b.word.length - a.word.length) || a.word.localeCompare(b.word));
    if (topN > 0) items = items.slice(0, topN);

    resultsDiv.innerHTML = renderResults(items, showPaths, oneBased);
    status.textContent = `Found ${found.size.toLocaleString()} words. Showing ${items.length.toLocaleString()}.`;
  } catch (err) {
    status.textContent = `Error: ${err.message}`;
  }
});
EOF
